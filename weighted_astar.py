import heapq
from A_estrela import haversine


def busca_weighted_a_estrela(
    grafo,
    coordenadas,
    origem,
    destino,
    peso=1.14
):
    """
    Weighted A* com cota teorica de subotimalidade.

    A heuristica e reduzida em 0.1% para maior margem numerica.
    Com peso=1.14, a cota teorica e de 14% acima do otimo,
    sob as condicoes de admissibilidade da heuristica.

    Retorna caminho, distancia e quantidade de nos expandidos.
    """

    if peso < 1:
        raise ValueError("O peso deve ser maior ou igual a 1.")

    if origem == destino:
        return {
            "caminho": [origem],
            "distancia": 0.0,
            "expandidos": 0
        }

    lat_destino, lon_destino = coordenadas[destino]

    def heuristica(no):
        lat, lon = coordenadas[no]
        distancia_reta = haversine(
            lat, lon, lat_destino, lon_destino
        )
        return 0.999 * distancia_reta

    fronteira = [
        (peso * heuristica(origem), 0.0, origem)
    ]

    menor_custo = {origem: 0.0}
    predecessores = {}
    expandidos = 0

    while fronteira:
        prioridade, custo_atual, no_atual = heapq.heappop(
            fronteira
        )

        # Ignora entradas antigas da fila.
        if custo_atual > menor_custo.get(no_atual, float("inf")):
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

            return {
                "caminho": caminho,
                "distancia": custo_atual,
                "expandidos": expandidos
            }

        expandidos += 1

        for vizinho, distancia_aresta in grafo[no_atual].items():
            novo_custo = custo_atual + distancia_aresta

            if (
                vizinho not in menor_custo
                or novo_custo < menor_custo[vizinho]
            ):
                menor_custo[vizinho] = novo_custo
                predecessores[vizinho] = no_atual

                nova_prioridade = (
                    novo_custo + peso * heuristica(vizinho)
                )

                heapq.heappush(
                    fronteira,
                    (nova_prioridade, novo_custo, vizinho)
                )

    return None
