
import heapq

def busca_custo_uniforme(grafo, origem, destino):

    fronteira = []
    heapq.heappush(fronteira, (0, origem))

    menor_custo = {origem: 0}
    predecessores = {}
    expandidos = 0

    while fronteira:

        custo_atual, no_atual = heapq.heappop(fronteira)

        # Ignora caminhos que já foram superados
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

        # Contabiliza a expansão
        expandidos += 1

        # Explora os vizinhos do nó atual
        for vizinho, distancia in grafo[no_atual].items():

            novo_custo = custo_atual + distancia

            if vizinho not in menor_custo or novo_custo < menor_custo[vizinho]:

                menor_custo[vizinho] = novo_custo
                predecessores[vizinho] = no_atual

                heapq.heappush(fronteira, (novo_custo, vizinho))

    return None
