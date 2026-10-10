import random
from time import perf_counter
from math import isclose
import pandas as pd

import sys
from pathlib import Path

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela

print("Carregando grafo...")
grafo = carregar_grafo()

nos = pd.read_csv("nos.csv")
coordenadas = {
    int(row.osmid): (row.latitude, row.longitude)
    for row in nos.itertuples(index=False)
}

random.seed(2026)
ids = sorted(set(grafo) & set(coordenadas))
amostra = random.sample(ids, min(20, len(ids)))
pares = list(zip(amostra[::2], amostra[1::2]))

print(f"\nTestando {len(pares)} pares de origem/destino\n")

total_exp_ucs = 0
total_exp_astar = 0
tempo_total_ucs = 0.0
tempo_total_astar = 0.0
validos = 0

for i, (origem, destino) in enumerate(pares, 1):
    inicio = perf_counter()
    resultado_ucs = busca_custo_uniforme(grafo, origem, destino)
    tempo_ucs = perf_counter() - inicio

    inicio = perf_counter()
    resultado_astar = busca_a_estrela(
        grafo, coordenadas, origem, destino
    )
    tempo_astar = perf_counter() - inicio

    print(f"--- Par {i}: {origem} -> {destino} ---")

    if resultado_ucs is None or resultado_astar is None:
        print("Uma ou ambas as buscas nao encontraram rota.\n")
        continue

    distancia_ucs = resultado_ucs["distancia"]
    distancia_astar = resultado_astar["distancia"]
    exp_ucs = resultado_ucs["expandidos"]
    exp_astar = resultado_astar["expandidos"]

    otimas = isclose(
        distancia_ucs, distancia_astar,
        rel_tol=1e-9, abs_tol=1e-5
    )

    reducao = (
        100 * (exp_ucs - exp_astar) / exp_ucs
        if exp_ucs else 0
    )

    print(f"Distancia UCS: {distancia_ucs:.2f} m")
    print(f"Distancia A*:  {distancia_astar:.2f} m")
    print(f"Distancias coincidem: {otimas}")
    print(f"Expansoes UCS: {exp_ucs}")
    print(f"Expansoes A*:  {exp_astar}")
    print(f"Reducao de expansoes: {reducao:.2f}%")
    print(f"Tempo UCS: {tempo_ucs:.4f} s")
    print(f"Tempo A*:  {tempo_astar:.4f} s\n")

    total_exp_ucs += exp_ucs
    total_exp_astar += exp_astar
    tempo_total_ucs += tempo_ucs
    tempo_total_astar += tempo_astar
    validos += 1

print("=== RESUMO ===")
print(f"Pares validos: {validos}")

if validos:
    reducao_total = (
        100 * (total_exp_ucs - total_exp_astar) / total_exp_ucs
        if total_exp_ucs else 0
    )
    print(f"Expansoes totais UCS: {total_exp_ucs}")
    print(f"Expansoes totais A*:  {total_exp_astar}")
    print(f"Reducao total: {reducao_total:.2f}%")
    print(f"Tempo total UCS: {tempo_total_ucs:.4f} s")
    print(f"Tempo total A*:  {tempo_total_astar:.4f} s")
