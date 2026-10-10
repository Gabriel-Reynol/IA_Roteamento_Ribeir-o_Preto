import sys
from pathlib import Path

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))
import pandas as pd
from A_estrela import haversine

nos = pd.read_csv("nos.csv")
arestas = pd.read_csv("arestas.csv")

coordenadas = {
    int(linha["osmid"]): (
        float(linha["latitude"]),
        float(linha["longitude"])
    )
    for _, linha in nos.iterrows()
}

menor_margem = float("inf")
arestas_verificadas = 0
violacoes_haversine = 0
violacoes_heuristica = 0
pior_razao = 0.0
pior_aresta = None

for _, linha in arestas.iterrows():
    origem = int(linha["origem"])
    destino = int(linha["destino"])
    distancia = float(linha["distancia"])

    lat1, lon1 = coordenadas[origem]
    lat2, lon2 = coordenadas[destino]

    reta = haversine(lat1, lon1, lat2, lon2)
    heuristica_reduzida = 0.999 * reta

    margem = distancia - reta
    margem_reduzida = distancia - heuristica_reduzida

    menor_margem = min(menor_margem, margem)
    arestas_verificadas += 1

    if reta > distancia:
        violacoes_haversine += 1

    if heuristica_reduzida > distancia:
        violacoes_heuristica += 1

    if distancia > 0:
        razao = reta / distancia
        if razao > pior_razao:
            pior_razao = razao
            pior_aresta = (origem, destino, distancia, reta)

print("VERIFICACAO DA HEURISTICA")
print("-" * 55)
print(f"Arestas verificadas: {arestas_verificadas}")
print(f"Menor margem (aresta - linha reta): {menor_margem:.9f} m")
print(f"Arestas com linha reta maior que o peso: {violacoes_haversine}")
print(f"Arestas com heuristica reduzida maior que o peso: {violacoes_heuristica}")
print(f"Maior razao linha reta/peso da aresta: {pior_razao:.12f}")
print(f"Aresta da maior razao: {pior_aresta}")
print("-" * 55)

if violacoes_heuristica == 0:
    print("RESULTADO: a heuristica reduzida nao excede o peso de nenhuma aresta.")
else:
    print("RESULTADO: existem violacoes; precisamos ajustar a heuristica.")
