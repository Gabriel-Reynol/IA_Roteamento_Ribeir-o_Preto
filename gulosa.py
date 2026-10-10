
import heapq
from A_estrela import haversine


def busca_gulosa(grafo, coordenadas, origem, destino):
    fronteira = []
    predecessores = {}
    descobertos = {origem}
    expandidos = 0

    lat_destino, lon_destino = coordenadas[destino]

    def heuristica(no):
        lat, lon = coordenadas[no]
        return haversine(
            lat, lon, lat_destino, lon_destino
        )

    heapq.heappush(
        fronteira,
        (heuristica(origem), origem)
    )

    while fronteira:
        _, no_atual = heapq.heappop(fronteira)

        if no_atual == destino:
            caminho = []
            no = destino

            while no != origem:
                caminho.append(no)
                no = predecessores[no]

            caminho.append(origem)
            caminho.reverse()

            distancia_total = 0.0

            for a, b in zip(caminho, caminho[1:]):
                distancia_total += grafo[a][b]

            return {
                "caminho": caminho,
                "distancia": distancia_total,
                "expandidos": expandidos
            }

        expandidos += 1

        for vizinho in grafo[no_atual]:
            if vizinho not in descobertos:
                descobertos.add(vizinho)
                predecessores[vizinho] = no_atual

                heapq.heappush(
                    fronteira,
                    (heuristica(vizinho), vizinho)
                )

    return None
