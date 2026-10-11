import sys
import time
import csv
import tempfile
import webbrowser
from pathlib import Path

import pandas as pd
import folium

from PySide6.QtCore import QUrl, Qt
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QFormLayout, QGroupBox,
    QSplitter, QMessageBox, QStatusBar, QTabWidget, QTableWidget,
    QTableWidgetItem, QFileDialog, QProgressBar
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from grafo import carregar_grafo
from geometria_mapa import construir_linha
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela
from weighted_astar import busca_weighted_a_estrela
from beam_search import busca_beam
from busca_gulosa import busca_gulosa


BASE = Path(__file__).resolve().parent
ALGORITMOS = [
    "UCS",
    "A*",
    "Weighted A*",
    "Beam Search (k=10)",
    "Beam Search (k=25)",
    "Gulosa",
]


def carregar_dados():
    nos_df = pd.read_csv(BASE / "nos.csv")
    grafo = carregar_grafo()

    coordenadas = {
        int(l.osmid): (float(l.latitude), float(l.longitude))
        for l in nos_df.itertuples(index=False)
    }

    nos_validos = sorted(set(grafo) & set(coordenadas))
    return grafo, coordenadas, nos_validos


def executar_algoritmo(nome, grafo, coordenadas, origem, destino):
    if nome == "UCS":
        return busca_custo_uniforme(grafo, origem, destino)
    if nome == "A*":
        return busca_a_estrela(grafo, coordenadas, origem, destino)
    if nome == "Weighted A*":
        return busca_weighted_a_estrela(
            grafo, coordenadas, origem, destino, peso=1.14
        )
    if nome == "Beam Search (k=10)":
        return busca_beam(
            grafo, coordenadas, origem, destino, largura=10
        )
    if nome == "Beam Search (k=25)":
        return busca_beam(
            grafo, coordenadas, origem, destino, largura=25
        )
    if nome == "Gulosa":
        return busca_gulosa(grafo, coordenadas, origem, destino)
    raise ValueError(f"Algoritmo desconhecido: {nome}")


class GraficoCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.figura = Figure(figsize=(13, 8), tight_layout=True)
        super().__init__(self.figura)
        self.setParent(parent)

    def desenhar(self, resultados):
        self.figura.clear()
        eixos = self.figura.subplots(2, 2)

        nomes = [r["algoritmo"] for r in resultados]

        cores_d1 = [
            "#16a34a" if r.get("desafio_1") == "Aprovado"
            else "#dc2626" if r.get("sucesso")
            else "#94a3b8"
            for r in resultados
        ]

        cores_d2 = [
            "#16a34a" if r.get("desafio_2") == "Aprovado"
            else "#dc2626" if r.get("sucesso")
            else "#94a3b8"
            for r in resultados
        ]

        # 1. Tempo de busca
        tempos_ms = [r["tempo_s"] * 1000 for r in resultados]
        barras = eixos[0, 0].barh(nomes, tempos_ms, color=cores_d1)
        eixos[0, 0].set_title("Tempo de busca")
        eixos[0, 0].set_xlabel("Tempo (ms)")
        eixos[0, 0].invert_yaxis()
        eixos[0, 0].bar_label(barras, fmt="%.2f ms", padding=3, fontsize=8)
        eixos[0, 0].margins(x=0.18)

        # 2. N?s expandidos: escala logar?tmica facilita comparar
        # algoritmos que expandem dezenas com os que expandem milhares.
        expandidos = [
            r["expandidos"] if r.get("sucesso") else 0
            for r in resultados
        ]
        barras = eixos[0, 1].barh(nomes, expandidos, color=cores_d1)
        eixos[0, 1].set_title("N?s expandidos ? cores do Desafio 1")
        eixos[0, 1].set_xlabel("N?s expandidos (escala logar?tmica)")
        if any(v > 0 for v in expandidos):
            eixos[0, 1].set_xscale("symlog", linthresh=1)
        eixos[0, 1].invert_yaxis()
        for barra, valor in zip(barras, expandidos):
            rotulo = str(valor) if valor > 0 else "sem rota"
            eixos[0, 1].annotate(
                rotulo,
                (barra.get_width(), barra.get_y() + barra.get_height() / 2),
                xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=8
            )
        eixos[0, 1].margins(x=0.22)

        # 3. Dist?ncia encontrada: falhas n?o s?o desenhadas como dist?ncia zero.
        referencia = next(
            (
                r["distancia_otima_km"]
                for r in resultados
                if r.get("distancia_otima_km") is not None
            ),
            None,
        )

        distancias = [
            r["distancia_km"] if r.get("sucesso") else 0
            for r in resultados
        ]
        barras = eixos[1, 0].barh(nomes, distancias, color=cores_d1)
        eixos[1, 0].set_title("Dist?ncia encontrada")
        eixos[1, 0].set_xlabel("Dist?ncia (km)")
        eixos[1, 0].invert_yaxis()

        if referencia is not None:
            eixos[1, 0].axvline(
                referencia, color="#7c3aed", linestyle="--",
                linewidth=2, label=f"?timo: {referencia:.3f} km"
            )
            eixos[1, 0].legend(fontsize=8)

        for barra, r in zip(barras, resultados):
            if r.get("sucesso"):
                rotulo = f'{r["distancia_km"]:.3f}'
                x = barra.get_width()
            else:
                rotulo = "sem rota"
                x = 0
            eixos[1, 0].annotate(
                rotulo,
                (x, barra.get_y() + barra.get_height() / 2),
                xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=8
            )
        eixos[1, 0].margins(x=0.22)

        # 4. Excesso percentual: zero ? um resultado v?lido.
        excessos = [
            r["excesso_percentual"]
            if r.get("sucesso") and r.get("excesso_percentual") is not None
            else 0
            for r in resultados
        ]
        barras = eixos[1, 1].barh(nomes, excessos, color=cores_d2)
        eixos[1, 1].axvline(
            15, color="#7c3aed", linestyle="--",
            linewidth=2, label="Limite: 15%"
        )
        eixos[1, 1].set_title("Excesso sobre a dist?ncia ?tima")
        eixos[1, 1].set_xlabel("Excesso (%)")
        eixos[1, 1].legend(fontsize=8)
        eixos[1, 1].invert_yaxis()

        for barra, r in zip(barras, resultados):
            if r.get("sucesso") and r.get("excesso_percentual") is not None:
                valor = r["excesso_percentual"]
                rotulo = f"{valor:.2f}%"
                x = barra.get_width()
            else:
                rotulo = "sem rota"
                x = 0
            eixos[1, 1].annotate(
                rotulo,
                (x, barra.get_y() + barra.get_height() / 2),
                xytext=(4, 0), textcoords="offset points",
                va="center", fontsize=8
            )
        eixos[1, 1].margins(x=0.22)

        for linha in eixos:
            for eixo in linha:
                eixo.grid(axis="x", alpha=0.25)
                eixo.set_axisbelow(True)

        self.figura.tight_layout(pad=2.0)
        self.draw()


class JanelaPrincipal(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Laboratório de Roteamento — Ribeirão Preto")
        self.resize(1450, 900)
        self.setStatusBar(QStatusBar())
        self.resultados_comparacao = []
        self.arquivo_mapa = None

        try:
            self.grafo, self.coordenadas, self.nos = carregar_dados()
        except Exception as erro:
            QMessageBox.critical(self, "Erro ao carregar dados", str(erro))
            raise

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        titulo = QLabel("Laboratório de Roteamento")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Ribeirão Preto • algoritmos locais • mapa de ruas via internet"
        )
        layout.addWidget(subtitulo)

        divisor = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(divisor, 1)

        painel = QWidget()
        painel.setMinimumWidth(320)
        painel_layout = QVBoxLayout(painel)

        grupo = QGroupBox("Configuração da busca")
        formulario = QFormLayout(grupo)

        self.origem = QComboBox()
        self.destino = QComboBox()
        for no in self.nos:
            self.origem.addItem(str(no), no)
            self.destino.addItem(str(no), no)

        if len(self.nos) > 1:
            self.destino.setCurrentIndex(1)

        self.algoritmo = QComboBox()
        self.algoritmo.addItems(ALGORITMOS)

        formulario.addRow("Origem (OSMID):", self.origem)
        formulario.addRow("Destino (OSMID):", self.destino)
        formulario.addRow("Algoritmo:", self.algoritmo)
        painel_layout.addWidget(grupo)

        self.botao_calcular = QPushButton("Calcular rota")
        self.botao_calcular.clicked.connect(self.calcular_rota)
        painel_layout.addWidget(self.botao_calcular)

        self.botao_comparar = QPushButton("Comparar todos (atalho para Testes)")
        self.botao_comparar.clicked.connect(self.comparar_algoritmos)
        painel_layout.addWidget(self.botao_comparar)

        self.botao_exportar = QPushButton("Exportar comparação para CSV")
        self.botao_exportar.clicked.connect(self.exportar_csv)
        self.botao_exportar.setEnabled(False)
        painel_layout.addWidget(self.botao_exportar)

        self.resultados = QLabel(
            "Selecione a origem e o destino e calcule uma rota."
        )
        self.resultados.setWordWrap(True)
        self.resultados.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.resultados.setStyleSheet(
            "QLabel { color: #17202a; background: #f0f3f6; "
            "border: 1px solid #cbd5e1; border-radius: 8px; padding: 12px; }"
        )
        painel_layout.addWidget(self.resultados)

        self.progresso = QProgressBar()
        self.progresso.setRange(0, 100)
        self.progresso.setValue(0)
        self.progresso.setVisible(False)
        painel_layout.addWidget(self.progresso)
        painel_layout.addStretch()

        abas = QTabWidget()

        # Mapa permanece disponível em uma aba própria.
        self.mapa = QWebEngineView()
        config = self.mapa.settings()
        config.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        config.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        self.mapa.loadFinished.connect(self.mapa_carregado)
        abas.addTab(self.mapa, "Mapa")

        # Desafio 1: UCS, A* ou comparação direta.
        d1 = QWidget(); d1l = QVBoxLayout(d1)
        d1l.addWidget(QLabel("DESAFIO 1 — A ROTA ÓTIMA\nUCS é a referência de menor distância. Compare a distância e os nós expandidos."))
        botoes1 = QHBoxLayout()
        b_ucs = QPushButton("Executar UCS"); b_ucs.clicked.connect(lambda: self.executar_desafio("UCS"))
        b_astar = QPushButton("Executar A*"); b_astar.clicked.connect(lambda: self.executar_desafio("A*"))
        b_comp = QPushButton("Comparar UCS × A*"); b_comp.clicked.connect(self.comparar_desafio1)
        for b in (b_ucs, b_astar, b_comp): botoes1.addWidget(b)
        d1l.addLayout(botoes1)
        self.saida_d1 = QLabel("Selecione origem e destino no painel à esquerda."); self.saida_d1.setWordWrap(True)
        d1l.addWidget(self.saida_d1); d1l.addStretch()
        abas.addTab(d1, "Desafio 1 — Ótima")

        # Desafio 2: Weighted A* fixo em 1.14 contra UCS.
        d2 = QWidget(); d2l = QVBoxLayout(d2)
        d2l.addWidget(QLabel("DESAFIO 2 — A ROTA EXPRESSA\nWeighted A* usa peso fixo 1,14. A rota é válida se o excesso sobre o UCS for de até 15%."))
        b_w = QPushButton("Executar Weighted A* (peso 1,14)"); b_w.clicked.connect(self.executar_desafio2)
        d2l.addWidget(b_w)
        self.saida_d2 = QLabel("A distância ótima será calculada pelo UCS para referência."); self.saida_d2.setWordWrap(True)
        d2l.addWidget(self.saida_d2); d2l.addStretch()
        abas.addTab(d2, "Desafio 2 — Expressa")

        # Experimentos e gráficos ficam isolados da avaliação dos desafios.
        testes = QWidget(); tl = QVBoxLayout(testes)
        tl.addWidget(QLabel("TESTES EXPERIMENTAIS — algoritmos adicionais, tabela e gráficos"))
        self.botao_testes = QPushButton("Comparar todos os algoritmos")
        self.botao_testes.clicked.connect(self.comparar_algoritmos); tl.addWidget(self.botao_testes)
        self.graficos = GraficoCanvas(self); tl.addWidget(self.graficos, 2)
        self.tabela = QTableWidget(0, 5)
        self.tabela.setHorizontalHeaderLabels(["Algoritmo", "Distância (km)", "Tempo (ms)", "Expandidos", "Nós no caminho"])
        self.tabela.horizontalHeader().setStretchLastSection(True); tl.addWidget(self.tabela, 1)
        abas.addTab(testes, "Testes")

        divisor.addWidget(painel)
        divisor.addWidget(abas)
        divisor.setSizes([370, 1050])

        self.abas = abas
        self.criar_mapa()

        self.statusBar().showMessage(
            f"{len(self.nos):,} nós carregados".replace(",", ".")
        )
    def mapa_carregado(self, sucesso):
        if sucesso:
            self.statusBar().showMessage(
                "Página do mapa carregada."
            )
        else:
            self.statusBar().showMessage(
                "Falha ao carregar a página do mapa."
            )

    def criar_mapa(self, caminho=None, origem=None, destino=None):
        pontos = list(self.coordenadas.values())
        centro = (
            sum(p[0] for p in pontos) / len(pontos),
            sum(p[1] for p in pontos) / len(pontos),
        )

        mapa = folium.Map(
            location=centro,
            zoom_start=13,
            tiles="OpenStreetMap",
            control_scale=True,
            prefer_canvas=True,
        )

        if caminho:
            coordenadas_rota = construir_linha(
                caminho, self.coordenadas
            )

            if coordenadas_rota:
                folium.PolyLine(
                    coordenadas_rota,
                    color="#2563eb",
                    weight=6,
                    opacity=0.9,
                    tooltip="Rota calculada",
                ).add_to(mapa)

                folium.Marker(
                    coordenadas_rota[0],
                    tooltip=f"Origem: {origem}",
                    icon=folium.Icon(color="green", icon="play"),
                ).add_to(mapa)

                folium.Marker(
                    coordenadas_rota[-1],
                    tooltip=f"Destino: {destino}",
                    icon=folium.Icon(color="red", icon="flag"),
                ).add_to(mapa)

                if len(coordenadas_rota) > 1:
                    mapa.fit_bounds(coordenadas_rota)

        arquivo = tempfile.NamedTemporaryFile(
            prefix="roteamento_",
            suffix=".html",
            delete=False,
        )
        arquivo.close()
        mapa.save(arquivo.name)
        self.arquivo_mapa = arquivo.name
        self.mapa.setUrl(QUrl.fromLocalFile(arquivo.name))

    def obter_par(self):
        return int(self.origem.currentData()), int(self.destino.currentData())

    def calcular_rota(self):
        origem, destino = self.obter_par()
        algoritmo = self.algoritmo.currentText()

        if origem == destino:
            QMessageBox.information(
                self, "Origem e destino", "Escolha nós diferentes."
            )
            return

        self.botao_calcular.setEnabled(False)
        self.statusBar().showMessage("Calculando rota...")
        QApplication.processEvents()

        try:
            inicio = time.perf_counter()
            resultado = executar_algoritmo(
                algoritmo, self.grafo, self.coordenadas, origem, destino
            )
            duracao = time.perf_counter() - inicio

            if not resultado:
                self.resultados.setText("Nenhuma rota encontrada.")
                self.criar_mapa()
                return

            caminho = resultado["caminho"]
            distancia = float(resultado["distancia"])
            expandidos = int(resultado["expandidos"])

            self.resultados.setText(
                f"Algoritmo: {algoritmo}\n\n"
                f"Distância: {distancia / 1000:.3f} km\n"
                f"Nós no caminho: {len(caminho)}\n"
                f"Nós expandidos: {expandidos:,}\n"
                f"Tempo de busca: {duracao * 1000:.3f} ms\n\n"
                f"Origem: {origem}\nDestino: {destino}".replace(",", ".")
            )
            self.criar_mapa(caminho, origem, destino)
            self.statusBar().showMessage(f"Rota calculada por {algoritmo}.")
            self.abas.setCurrentIndex(0)

        except Exception as erro:
            QMessageBox.critical(self, "Erro ao calcular rota", str(erro))
        finally:
            self.botao_calcular.setEnabled(True)

    def _medir(self, nome, origem, destino):
        inicio = time.perf_counter()
        resultado = executar_algoritmo(nome, self.grafo, self.coordenadas, origem, destino)
        return resultado, time.perf_counter() - inicio

    def executar_desafio(self, nome):
        origem, destino = self.obter_par()
        if origem == destino:
            QMessageBox.information(self, "Origem e destino", "Escolha nós diferentes."); return
        try:
            ref, tr = self._medir("UCS", origem, destino)
            res, tempo = self._medir(nome, origem, destino)
            if not ref or not res:
                self.saida_d1.setText("Não foi encontrada uma rota para este par."); return
            otima = float(ref["distancia"]); dist = float(res["distancia"])
            status = "APROVADO — distância ótima" if abs(dist-otima) <= max(1e-6, otima*1e-9) else "FORA DO ÓTIMO"
            self.saida_d1.setText(f"Algoritmo: {nome}\nResultado: {status}\nDistância encontrada: {dist/1000:.3f} km\nNós expandidos: {res['expandidos']}\nNós no caminho: {len(res['caminho'])}\nTempo: {tempo*1000:.3f} ms\nTempo de referência UCS: {tr*1000:.3f} ms")
            self.criar_mapa(res["caminho"], origem, destino)
        except Exception as e: QMessageBox.critical(self, "Erro no Desafio 1", str(e))

    def comparar_desafio1(self):
        origem, destino = self.obter_par()
        if origem == destino:
            QMessageBox.information(self, "Origem e destino", "Escolha nós diferentes."); return
        try:
            u, tu = self._medir("UCS", origem, destino); a, ta = self._medir("A*", origem, destino)
            if not u or not a: self.saida_d1.setText("Não foi encontrada uma rota."); return
            d=float(u["distancia"]); da=float(a["distancia"])
            self.saida_d1.setText(f"Comparação UCS × A*\nDistância ótima (UCS): {d/1000:.3f} km\nUCS — expandidos: {u['expandidos']} | tempo: {tu*1000:.3f} ms\nA* — distância: {da/1000:.3f} km | expandidos: {a['expandidos']} | tempo: {ta*1000:.3f} ms\nMenos expansões: {'UCS' if u['expandidos'] < a['expandidos'] else 'A*' if a['expandidos'] < u['expandidos'] else 'empate'}")
            self.criar_mapa(a["caminho"], origem, destino)
        except Exception as e: QMessageBox.critical(self, "Erro na comparação", str(e))

    def executar_desafio2(self):
        origem, destino = self.obter_par()
        if origem == destino:
            QMessageBox.information(self, "Origem e destino", "Escolha nós diferentes."); return
        try:
            u, tu = self._medir("UCS", origem, destino); w, tw = self._medir("Weighted A*", origem, destino)
            if not u or not w: self.saida_d2.setText("Não foi encontrada uma rota."); return
            d=float(u["distancia"]); dw=float(w["distancia"]); excesso=(dw-d)/d*100 if d else 0
            valido = excesso <= 15.0 + 1e-9
            self.saida_d2.setText(f"Weighted A* — peso fixo 1,14\nResultado: {'APROVADO' if valido else 'REPROVADO'} (limite: 15%)\nDistância encontrada: {dw/1000:.3f} km\nDistância ótima (UCS): {d/1000:.3f} km\nExcesso: {excesso:.3f}%\nNós expandidos: {w['expandidos']}\nNós no caminho: {len(w['caminho'])}\nTempo Weighted A*: {tw*1000:.3f} ms\nTempo UCS de referência: {tu*1000:.3f} ms")
            self.criar_mapa(w["caminho"], origem, destino)
        except Exception as e: QMessageBox.critical(self, "Erro no Desafio 2", str(e))

    def comparar_algoritmos(self):
        origem, destino = self.obter_par()

        if origem == destino:
            QMessageBox.information(
                self, "Origem e destino", "Escolha n?s diferentes."
            )
            return

        self.botao_comparar.setEnabled(False)
        self.botao_calcular.setEnabled(False)
        self.progresso.setVisible(True)
        self.progresso.setValue(0)
        QApplication.processEvents()

        resultados = []

        try:
            # UCS fornece a refer?ncia de dist?ncia ?tima.
            inicio_ucs = time.perf_counter()
            referencia = busca_custo_uniforme(
                self.grafo, origem, destino
            )
            tempo_ucs = time.perf_counter() - inicio_ucs

            if not referencia:
                QMessageBox.warning(
                    self, "Sem rota",
                    "O UCS n?o encontrou uma rota para este par."
                )
                return

            distancia_otima = float(referencia["distancia"])
            tolerancia = max(1e-6, abs(distancia_otima) * 1e-9)

            for indice, nome in enumerate(ALGORITMOS):
                QApplication.processEvents()
                inicio_busca = time.perf_counter()
                erro = ""

                try:
                    resultado = executar_algoritmo(
                        nome, self.grafo, self.coordenadas,
                        origem, destino
                    )
                except Exception as exc:
                    resultado = None
                    erro = str(exc)

                duracao = time.perf_counter() - inicio_busca
                sucesso = bool(resultado)
                distancia = (
                    float(resultado["distancia"]) if sucesso else None
                )
                expandidos = (
                    int(resultado["expandidos"]) if sucesso else None
                )

                excesso = None
                desafio_1 = "Reprovado"
                desafio_2 = "Reprovado"

                if sucesso:
                    excesso = (
                        (distancia - distancia_otima)
                        / distancia_otima * 100
                    ) if distancia_otima > 0 else (
                        0.0 if abs(distancia) <= tolerancia else None
                    )

                    if abs(distancia - distancia_otima) <= tolerancia:
                        desafio_1 = "Aprovado"

                    if excesso is not None and excesso <= 15.0 + 1e-9:
                        desafio_2 = "Aprovado"

                resultados.append({
                    "algoritmo": nome,
                    "origem": origem,
                    "destino": destino,
                    "sucesso": sucesso,
                    "distancia_otima_km": distancia_otima / 1000,
                    "distancia_km": (
                        distancia / 1000 if sucesso else None
                    ),
                    "excesso_percentual": excesso,
                    "desafio_1": desafio_1,
                    "desafio_2": desafio_2,
                    "tempo_s": duracao,
                    "expandidos": expandidos,
                    "nos_caminho": (
                        len(resultado["caminho"]) if sucesso else None
                    ),
                    "erro": erro or (
                        "" if sucesso else "Rota n?o encontrada"
                    ),
                })

                self.progresso.setValue(
                    int((indice + 1) * 100 / len(ALGORITMOS))
                )
                QApplication.processEvents()

            self.resultados_comparacao = resultados

            # Atualiza a tabela com os crit?rios oficiais dos desafios.
            colunas = [
                "Algoritmo", "?tima (km)", "Dist?ncia (km)",
                "Excesso (%)", "Tempo (ms)", "Expandidos",
                "N?s no caminho", "Desafio 1", "Desafio 2"
            ]
            self.tabela.setColumnCount(len(colunas))
            self.tabela.setHorizontalHeaderLabels(colunas)
            self.tabela.setRowCount(len(resultados))

            for i, r in enumerate(resultados):
                valores = [
                    r["algoritmo"],
                    f'{r["distancia_otima_km"]:.3f}',
                    f'{r["distancia_km"]:.3f}'
                    if r["sucesso"] else "?",
                    f'{r["excesso_percentual"]:.3f}'
                    if r["excesso_percentual"] is not None else "?",
                    f'{r["tempo_s"] * 1000:.3f}',
                    str(r["expandidos"])
                    if r["sucesso"] else "?",
                    str(r["nos_caminho"])
                    if r["sucesso"] else "?",
                    r["desafio_1"],
                    r["desafio_2"],
                ]
                for j, valor in enumerate(valores):
                    self.tabela.setItem(i, j, QTableWidgetItem(valor))

            self.tabela.resizeColumnsToContents()
            self.graficos.desenhar(resultados)
            self.abas.setCurrentIndex(1)

            validos = [r for r in resultados if r["sucesso"]]
            aprovados_1 = [
                r for r in validos if r["desafio_1"] == "Aprovado"
            ]
            aprovados_2 = [
                r for r in validos if r["desafio_2"] == "Aprovado"
            ]

            resumo = [
                f"Compara??o conclu?da: {len(validos)}/{len(resultados)} encontraram rota.",
                f"Origem: {origem}",
                f"Destino: {destino}",
                f"Dist?ncia ?tima (UCS): {distancia_otima / 1000:.3f} km",
                f"Desafio 1 ? rotas ?timas: {len(aprovados_1)}",
                f"Desafio 2 ? rotas dentro de 15%: {len(aprovados_2)}",
                "",
                f"Tempo da refer?ncia UCS: {tempo_ucs * 1000:.3f} ms",
                "Os tempos variam entre execu??es e s?o m?tricas complementares.",
            ]

            if aprovados_1:
                melhor = min(aprovados_1, key=lambda r: r["expandidos"])
                resumo.append(
                    f"Desafio 1 ? menor expans?o: {melhor['algoritmo']} "
                    f"({melhor['expandidos']} n?s)"
                )

            if aprovados_2:
                melhor = min(aprovados_2, key=lambda r: r["expandidos"])
                resumo.append(
                    f"Desafio 2 ? menor expans?o: {melhor['algoritmo']} "
                    f"({melhor['expandidos']} n?s)"
                )

            self.resultados.setText("\n".join(resumo))
            self.botao_exportar.setEnabled(True)
            self.statusBar().showMessage("Compara??o conclu?da.")

        except Exception as erro:
            QMessageBox.critical(self, "Erro na compara??o", str(erro))
        finally:
            self.progresso.setVisible(False)
            self.botao_comparar.setEnabled(True)
            self.botao_calcular.setEnabled(True)

    def exportar_csv(self):
        if not self.resultados_comparacao:
            return

        caminho, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar resultados",
            str(BASE / "comparacao_algoritmos.csv"),
            "CSV (*.csv)",
        )
        if not caminho:
            return

        colunas = [
            "algoritmo", "origem", "destino", "sucesso",
            "distancia_otima_km", "distancia_km",
            "excesso_percentual", "desafio_1", "desafio_2",
            "tempo_s", "expandidos", "nos_caminho", "erro"
        ]
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo_csv:
                escritor = csv.DictWriter(arquivo_csv, fieldnames=colunas)
                escritor.writeheader()
                escritor.writerows(self.resultados_comparacao)

            QMessageBox.information(
                self, "Exporta??o conclu?da",
                f"Arquivo salvo em:\n{caminho}"
            )
        except Exception as erro:
            QMessageBox.critical(self, "Erro ao exportar", str(erro))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    janela = JanelaPrincipal()
    janela.show()
    sys.exit(app.exec())
