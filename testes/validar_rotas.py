import random
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

def validar_rota(nome, resultado, origem, destino):
    erros = []

    if resultado is None:
        print(f"  {nome}: nenhuma rota encontrada.")
        return False

    caminho = resultado["caminho"]

    if not caminho:
        erros.append("caminho vazio")
    else:
        if caminho[0] != origem:
            erros.append("caminho nao comeca na origem")
        if caminho[-1] != destino:
            erros.append("caminho nao termina no destino")

    soma = 0.0

    for a, b in zip(caminho, caminho[1:]):
        if a not in grafo or b not in grafo[a]:
            erros.append(f"aresta inexistente: {a} -> {b}")
            break
        soma += grafo[a][b]

    if not isclose(
        soma, resultado["distancia"],
        rel_tol=1e-9, abs_tol=1e-5
    ):
        erros.append(
            f"soma das arestas ({soma:.5f}) diferente "
            f"da distancia informada ({resultado['distancia']:.5f})"
        )

    if erros:
        print(f"  {nome}: FALHOU")
        for erro in erros:
            print(f"    - {erro}")
        return False

    print(
        f"  {nome}: OK | {len(caminho)} nos no caminho | "
        f"{resultado['distancia']:.2f} m"
    )
    return True

random.seed(2026)
ids = sorted(set(grafo) & set(coordenadas))
amostra = random.sample(ids, min(20, len(ids)))
pares = list(zip(amostra[::2], amostra[1::2]))

total_testes = 0
total_aprovados = 0

print(f"\nValidando {len(pares)} pares de origem/destino...\n")

for i, (origem, destino) in enumerate(pares, 1):
    print(f"Par {i}: {origem} -> {destino}")

    resultados = [
        ("UCS", busca_custo_uniforme(grafo, origem, destino)),
        ("A*", busca_a_estrela(grafo, coordenadas, origem, destino))
    ]

    for nome, resultado in resultados:
        total_testes += 1
        if validar_rota(nome, resultado, origem, destino):
            total_aprovados += 1

print("\n=== RESUMO DA VALIDACAO ===")
print(f"Testes aprovados: {total_aprovados}/{total_testes}")

if total_aprovados == total_testes:
    print("Todas as rotas passaram nas verificacoes.")
else:
    print("ATENCAO: existem rotas que precisam ser investigadas.")
