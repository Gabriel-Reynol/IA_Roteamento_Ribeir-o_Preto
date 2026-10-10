import heapq
from A_estrela import haversine


def busca_beam(grafo, coordenadas, origem, destino, largura=25):
    """
    Beam Search guiado pela distancia em linha reta ate o destino.

    largura (k): numero maximo de candidatos mantidos por nivel.
    Nao garante otimalidade nem limite de excesso de 15%.
    """

    if largura < 1:
        raise ValueError("A largura do feixe deve ser >= 1.")

    if origem not in grafo or destino not in grafo:
        return None

    if origem not in coordenadas or destino not in coordenadas:
        return None

    if origem == destino:
        return {
            "caminho": [origem],
            "distancia": 0.0,
            "expandidos": 0
        }

    lat_destino, lon_destino = coordenadas[destino]

    def heuristica(no):
        lat, lon = coordenadas[no]
        return haversine(lat, lon, lat_destino, lon_destino)

    # Cada estado guarda: (heuristica, custo acumulado, no, caminho).
    feixe = [
        (heuristica(origem), 0.0, origem, (origem,))
    ]

    expandidos = 0

    while feixe:
        candidatos = {}

        for _, custo_atual, no_atual, caminho in feixe:
            # O destino termina a busca sem contar como expandido.
            if no_atual == destino:
                return {
                    "caminho": list(caminho),
                    "distancia": custo_atual,
                    "expandidos": expandidos
                }

            expandidos += 1

            for vizinho, distancia_aresta in grafo[no_atual].items():
                # Evita ciclos dentro do mesmo caminho.
                if vizinho in caminho:
                    continue

                novo_custo = custo_atual + distancia_aresta
                novo_caminho = caminho + (vizinho,)

                if vizinho == destino:
                    candidatos[vizinho] = (
                        heuristica(vizinho),
                        novo_custo,
                        vizinho,
                        novo_caminho
                    )
                    continue

                candidato = (
                    heuristica(vizinho),
                    novo_custo,
                    vizinho,
                    novo_caminho
                )

                anterior = candidatos.get(vizinho)

                # Para o mesmo no neste nivel, conserva o caminho
                # de menor custo acumulado.
                if anterior is None or novo_custo < anterior[1]:
                    candidatos[vizinho] = candidato

        if not candidatos:
            return None

        # Prioriza proximidade ao destino; em empate, menor custo.
        proximos = sorted(
            candidatos.values(),
            key=lambda estado: (estado[0], estado[1])
        )

        feixe = proximos[:largura]

    return None
