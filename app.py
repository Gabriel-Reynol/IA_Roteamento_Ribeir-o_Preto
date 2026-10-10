import time
from pathlib import Path

import pandas as pd
import streamlit as st
import folium
import plotly.express as px
from streamlit_folium import st_folium

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela
from weighted_astar import busca_weighted_a_estrela
from beam_search import busca_beam
from busca_gulosa import busca_gulosa


st.set_page_config(
    page_title="Laboratório de Roteamento",
    page_icon="🗺️",
    layout="wide",
)

DESCRICOES = {
    "A*": {
        "funcao": "Busca informada que combina o custo percorrido (g) "
                  "com uma estimativa da distância restante (h).",
        "criterio": "f(n) = g(n) + h(n)",
        "otimo": "Sim, com heurística admissível e as condições usuais da implementação.",
        "limite": "Não precisa de aproximação: busca a rota ótima.",
    },
    "Weighted A*": {
        "funcao": "Dá mais peso à estimativa até o destino para orientar "
                  "a busca de forma mais agressiva.",
        "criterio": "f(n) = g(n) + w × h(n), com w = 1.14.",
        "otimo": "Não necessariamente.",
        "limite": "A implementação foi projetada para uma cota teórica de 14%, "
                  "sob as condições de admissibilidade e implementação aplicáveis. "
                  "O limite deve ser validado nos dados reais.",
    },
    "Beam k=10": {
        "funcao": "Mantém uma quantidade limitada de candidatos por etapa, "
                  "priorizando os que parecem mais próximos do destino.",
        "criterio": "Largura da busca = 10.",
        "otimo": "Não.",
        "limite": "Não garante uma rota dentro de 15% do ótimo.",
    },
    "Gulosa": {
        "funcao": "Escolhe os candidatos pela estimativa da distância restante, "
                  "sem considerar o custo acumulado para priorizar a expansão.",
        "criterio": "f(n) = h(n).",
        "otimo": "Não.",
        "limite": "Não garante uma rota dentro de 15% do ótimo.",
    },
}

ALGORITMOS = {
    "A*": lambda grafo, coords, origem, destino: busca_a_estrela(
        grafo, coords, origem, destino
    ),
    "Weighted A*": lambda grafo, coords, origem, destino: (
        busca_weighted_a_estrela(grafo, coords, origem, destino, peso=1.14)
    ),
    "Beam k=10": lambda grafo, coords, origem, destino: busca_beam(
        grafo, coords, origem, destino, largura=10
    ),
    "Gulosa": lambda grafo, coords, origem, destino: busca_gulosa(
        grafo, coords, origem, destino
    ),
}

CORES = {
    "A*": "blue",
    "Weighted A*": "purple",
    "Beam k=10": "orange",
    "Gulosa": "darkgreen",
}


@st.cache_resource(show_spinner="Carregando o grafo de ruas...")
def carregar_dados():
    for nome in ("nos.csv", "arestas.csv"):
        if not Path(nome).exists():
            raise FileNotFoundError(
                f"Não encontrei {nome}. Abra a aplicação na pasta do projeto."
            )

    grafo = carregar_grafo()
    df_nos = pd.read_csv("nos.csv")

    coordenadas = {
        int(linha["osmid"]): (
            float(linha["latitude"]),
            float(linha["longitude"]),
        )
        for _, linha in df_nos.iterrows()
    }

    nos_validos = set(grafo) & set(coordenadas)
    return grafo, coordenadas, sorted(nos_validos)


def validar_rota(grafo, resultado, origem, destino):
    if resultado is None:
        return False, "O algoritmo não encontrou uma rota."

    caminho = resultado.get("caminho", [])
    if not caminho or caminho[0] != origem or caminho[-1] != destino:
        return False, "A rota não começa na origem ou termina no destino."

    distancia_real = 0.0
    for a, b in zip(caminho, caminho[1:]):
        if b not in grafo.get(a, {}):
            return False, f"A rota contém uma ligação inexistente: {a} → {b}."
        distancia_real += grafo[a][b]

    if abs(distancia_real - float(resultado["distancia"])) > 0.02:
        return False, "A distância retornada não confere com as arestas da rota."

    return True, "Rota válida."


def executar_medida(funcao, *args):
    inicio = time.perf_counter()
    resultado = funcao(*args)
    duracao = time.perf_counter() - inicio
    return resultado, duracao


def criar_mapa(coordenadas, origem, destino, resultados):
    pontos = [
        coordenadas[origem],
        coordenadas[destino],
    ]
    centro = (
        (pontos[0][0] + pontos[1][0]) / 2,
        (pontos[0][1] + pontos[1][1]) / 2,
    )

    mapa = folium.Map(location=centro, zoom_start=13, control_scale=True)

    folium.Marker(
        coordenadas[origem],
        tooltip=f"Origem: {origem}",
        popup=f"Nó de origem: {origem}",
        icon=folium.Icon(color="green", icon="play"),
    ).add_to(mapa)

    folium.Marker(
        coordenadas[destino],
        tooltip=f"Destino: {destino}",
        popup=f"Nó de destino: {destino}",
        icon=folium.Icon(color="red", icon="flag"),
    ).add_to(mapa)

    pontos_rotas = []
    for nome, dados in resultados.items():
        if not dados["valida"]:
            continue

        caminho = dados["resultado"]["caminho"]
        linha = [coordenadas[n] for n in caminho if n in coordenadas]
        if len(linha) < 2:
            continue

        cor = CORES.get(nome, "cadetblue")
        folium.PolyLine(
            linha,
            color=cor,
            weight=5,
            opacity=0.8,
            tooltip=(
                f"{nome} | {dados['distancia'] / 1000:.2f} km"
                f" | excesso {dados['excesso']:.2f}%"
            ),
        ).add_to(mapa)
        pontos_rotas.extend(linha)

    if pontos_rotas:
        mapa.fit_bounds(pontos_rotas)
    else:
        mapa.fit_bounds(pontos)

    return mapa


st.title("🗺️ Laboratório de Roteamento")
st.caption(
    "Ribeirão Preto • Experimentos com algoritmos de busca em grafo real"
)

try:
    grafo, coordenadas, nos = carregar_dados()
except Exception as erro:
    st.error(f"Falha ao carregar os dados do projeto: {erro}")
    st.stop()

with st.sidebar:
    st.header("Configuração do teste")
    st.caption(f"{len(nos):,} nós com coordenadas e conexões disponíveis")

    origem_padrao = 1827802528
    destino_padrao = 2191667380

    ids = [str(n) for n in nos]
    origem_texto = st.text_input("ID do nó de origem", str(origem_padrao))
    destino_texto = st.text_input("ID do nó de destino", str(destino_padrao))

    desafio = st.radio(
        "Objetivo",
        ["Rota expressa (até 15%)", "Rota ótima"],
        index=0,
    )

    selecionados = st.multiselect(
        "Algoritmos para comparar",
        list(ALGORITMOS.keys()),
        default=["A*", "Weighted A*", "Beam k=10", "Gulosa"],
    )

    executar = st.button("Executar comparação", type="primary", use_container_width=True)

st.info(
    "A rota ótima de referência é calculada pelo UCS em cada teste. "
    "Ela serve para medir o excesso percentual, mesmo quando UCS não está "
    "selecionado na lista de algoritmos."
)

if executar:
    try:
        origem = int(origem_texto.strip())
        destino = int(destino_texto.strip())
    except ValueError:
        st.error("Origem e destino precisam ser IDs numéricos inteiros.")
        st.stop()

    if origem not in nos or destino not in nos:
        st.error("Origem ou destino não existe no grafo com coordenadas.")
        st.stop()

    if origem == destino:
        st.warning("Origem e destino são iguais. Escolha dois nós diferentes.")
        st.stop()

    if not selecionados:
        st.warning("Selecione pelo menos um algoritmo.")
        st.stop()

    with st.spinner("Calculando a rota ótima de referência com UCS..."):
        referencia, tempo_ucs = executar_medida(
            busca_custo_uniforme, grafo, origem, destino
        )

    if referencia is None:
        st.error("O UCS não encontrou uma rota entre esses nós.")
        st.stop()

    distancia_otima = float(referencia["distancia"])
    limite_distancia = distancia_otima * 1.15

    st.session_state["ultimo_teste"] = {
        "origem": origem,
        "destino": destino,
        "selecionados": selecionados,
        "desafio": desafio,
        "distancia_otima": distancia_otima,
        "tempo_ucs": tempo_ucs,
    }

    resultados = {}
    for nome in selecionados:
        try:
            with st.spinner(f"Executando {nome}..."):
                resultado, duracao = executar_medida(
                    ALGORITMOS[nome], grafo, coordenadas, origem, destino
                )

            valida, mensagem = validar_rota(
                grafo, resultado, origem, destino
            )
            if not valida:
                resultados[nome] = {
                    "resultado": resultado,
                    "valida": False,
                    "mensagem": mensagem,
                    "tempo": duracao,
                    "distancia": None,
                    "expandidos": (
                        resultado.get("expandidos", 0)
                        if resultado else 0
                    ),
                    "excesso": None,
                }
                continue

            distancia = float(resultado["distancia"])
            excesso = (
                (distancia - distancia_otima) / distancia_otima * 100
                if distancia_otima > 0 else 0.0
            )
            resultados[nome] = {
                "resultado": resultado,
                "valida": True,
                "mensagem": mensagem,
                "tempo": duracao,
                "distancia": distancia,
                "expandidos": int(resultado.get("expandidos", 0)),
                "excesso": excesso,
            }
        except Exception as erro:
            resultados[nome] = {
                "resultado": None,
                "valida": False,
                "mensagem": f"Erro durante a execução: {erro}",
                "tempo": 0.0,
                "distancia": None,
                "expandidos": 0,
                "excesso": None,
            }

    st.session_state["resultados"] = resultados
    st.session_state["referencia"] = referencia

if "resultados" in st.session_state:
    dados_teste = st.session_state["ultimo_teste"]
    resultados = st.session_state["resultados"]
    distancia_otima = dados_teste["distancia_otima"]
    limite_distancia = distancia_otima * 1.15

    st.subheader("Resumo do teste")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Distância ótima (UCS)", f"{distancia_otima / 1000:.3f} km")
    c2.metric("Limite de 15%", f"{limite_distancia / 1000:.3f} km")
    c3.metric("Algoritmos selecionados", len(resultados))
    c4.metric("Tempo UCS de referência", f"{dados_teste['tempo_ucs'] * 1000:.2f} ms")

    st.subheader("Mapa das rotas")
    st.caption(
        "As linhas representam as sequências reais de nós retornadas pelos algoritmos. "
        "Se uma busca falhar, ela não será desenhada."
    )
    mapa = criar_mapa(
        coordenadas,
        dados_teste["origem"],
        dados_teste["destino"],
        resultados,
    )
    st_folium(mapa, use_container_width=True, height=600)

    linhas = []
    for nome, d in resultados.items():
        dentro = (
            d["valida"]
            and d["distancia"] <= limite_distancia + 0.01
        )
        linhas.append({
            "Algoritmo": nome,
            "Status": (
                "Válida" if d["valida"] else "Falha"
            ),
            "Distância (m)": (
                round(d["distancia"], 2) if d["valida"] else None
            ),
            "Excesso (%)": (
                round(d["excesso"], 3) if d["valida"] else None
            ),
            "Nós expandidos": d["expandidos"],
            "Tempo (ms)": round(d["tempo"] * 1000, 3),
            "Dentro de 15%": (
                "Sim" if dentro else ("Não" if d["valida"] else "—")
            ),
            "Detalhe": d["mensagem"],
        })

    df = pd.DataFrame(linhas)
    st.subheader("Tabela de resultados")
    st.dataframe(df, use_container_width=True, hide_index=True)

    validos = df[df["Status"] == "Válida"].copy()
    if not validos.empty:
        st.subheader("Comparação visual")

        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(
                validos,
                x="Algoritmo",
                y="Distância (m)",
                color="Algoritmo",
                title="Distância total por algoritmo",
            )
            fig.add_hline(
                y=distancia_otima,
                line_dash="dash",
                annotation_text="Ótimo (UCS)",
            )
            fig.add_hline(
                y=limite_distancia,
                line_dash="dot",
                annotation_text="Limite +15%",
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig = px.bar(
                validos,
                x="Algoritmo",
                y="Nós expandidos",
                color="Algoritmo",
                title="Nós expandidos",
            )
            st.plotly_chart(fig, use_container_width=True)

        fig = px.bar(
            validos,
            x="Algoritmo",
            y="Tempo (ms)",
            color="Algoritmo",
            title="Tempo de execução medido",
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Como funciona cada algoritmo")
        for nome in dados_teste["selecionados"]:
            with st.expander(nome):
                info = DESCRICOES[nome]
                st.write(info["funcao"])
                st.markdown(f"**Critério de prioridade:** `{info['criterio']}`")
                st.markdown(f"**Garante a rota ótima?** {info['otimo']}")
                st.markdown(f"**Garantia sobre 15%:** {info['limite']}")
                if nome in resultados:
                    d = resultados[nome]
                    if d["valida"]:
                        st.write(
                            f"Resultado real deste teste: "
                            f"{d['distancia']:.2f} m, "
                            f"{d['expandidos']} nós expandidos, "
                            f"{d['tempo'] * 1000:.3f} ms."
                        )
                    else:
                        st.warning(d["mensagem"])

    st.download_button(
        "Exportar resultados CSV",
        data=df.to_csv(index=False).encode("utf-8-sig"),
        file_name="resultados_roteamento.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Os resultados são calculados em tempo real com os CSVs e os módulos Python "
    "do projeto. Os tempos podem variar conforme a carga do computador."
)
