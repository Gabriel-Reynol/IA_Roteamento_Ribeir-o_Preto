import heapq

from math import radians, sin, cos, asin, sqrt

def haversine(lat1, lon1, lat2, lon2):

    # Converter graus para radianos
    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    # Diferença entre as coordenadas
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    # Fórmula de Haversine
    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1) * cos(lat2) * sin(delta_lon / 2) ** 2
    )

    c = 2 * asin(sqrt(a))

    raio_terra = 6371000  # Metros

    return raio_terra * c


def busca_a_estrela(grafo, coordenadas, origem, destino):

    fronteira = []
    menor_custo = {origem: 0}
    predecessores = {}
    expandidos = 0

    # Coordenadas do destino
    lat_destino, lon_destino = coordenadas[destino]

    def heuristica(no):
        lat, lon = coordenadas[no]

        return haversine(
            lat, lon,
            lat_destino, lon_destino
        )

    # Origem com custo acumulado zero
    heapq.heappush(fronteira, (heuristica(origem), 0, origem))

    while fronteira:

        prioridade, custo_atual, no_atual = heapq.heappop(fronteira)

        # Ignora caminhos superados
        if custo_atual > menor_custo[no_atual]:
            continue

        # Verifica se encontramos o destino
        if no_atual == destino:

            caminho = []
            no = destino

            while no != origem:
                caminho.append(no)
                no = predecessores[no]

            caminho.append(origem)
            caminho.reverse()

            return {
                "caminho": caminho,
                "distancia": custo_atual,
                "expandidos": expandidos
            }

        expandidos += 1

        # Explora os vizinhos
        for vizinho, distancia in grafo[no_atual].items():

            novo_custo = custo_atual + distancia

            if vizinho not in menor_custo or novo_custo < menor_custo[vizinho]:

                menor_custo[vizinho] = novo_custo
                predecessores[vizinho] = no_atual

                prioridade_vizinho = novo_custo + heuristica(vizinho)

                heapq.heappush(
                    fronteira,
                    (prioridade_vizinho, novo_custo, vizinho)
                )

    return None
