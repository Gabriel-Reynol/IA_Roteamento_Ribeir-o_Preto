import heapq
from A_estrela import haversine


def busca_gulosa(grafo, coordenadas, origem, destino):
    """
    Busca Gulosa Best-First Search.
    Prioriza apenas a distancia estimada ate o destino (h).
    Nao garante encontrar a rota otima.
    """

    if origem not in grafo or destino not in grafo:
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

    fronteira = [(heuristica(origem), origem)]
    predecessores = {}
    visitados = set()
    expandidos = 0

    while fronteira:
        _, no_atual = heapq.heappop(fronteira)

        if no_atual in visitados:
            continue

        # O destino nao conta como no expandido.
        if no_atual == destino:
            caminho = []
            no = destino

            while no != origem:
                caminho.append(no)
                no = predecessores[no]

            caminho.append(origem)
            caminho.reverse()

            distancia = sum(
                grafo[a][b] for a, b in zip(caminho, caminho[1:])
            )

            return {
                "caminho": caminho,
                "distancia": distancia,
                "expandidos": expandidos
            }

        visitados.add(no_atual)
        expandidos += 1

        for vizinho in grafo[no_atual]:
            if vizinho not in visitados:
                # Evita inserir o mesmo no varias vezes.
                if vizinho not in predecessores and vizinho != origem:
                    predecessores[vizinho] = no_atual
                    heapq.heappush(
                        fronteira,
                        (heuristica(vizinho), vizinho)
                    )

    return None
