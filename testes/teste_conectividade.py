import sys
from pathlib import Path

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))
from collections import deque
from grafo import carregar_grafo

grafo = carregar_grafo()
visitados = set()
componentes = []

for inicio in grafo:
    if inicio in visitados:
        continue

    fila = deque([inicio])
    visitados.add(inicio)
    tamanho = 0

    while fila:
        atual = fila.popleft()
        tamanho += 1

        for vizinho in grafo[atual]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

    componentes.append(tamanho)

componentes.sort(reverse=True)

print("=== CONECTIVIDADE DO GRAFO ===")
print(f"Total de nos: {len(grafo)}")
print(f"Componentes conexos: {len(componentes)}")
print(f"Maior componente: {componentes[0] if componentes else 0} nos")

print("\nTamanhos dos 10 maiores componentes:")
for i, tamanho in enumerate(componentes[:10], 1):
    print(f"{i}. {tamanho} nos")

if len(componentes) == 1:
    print("\nO grafo e totalmente conectado.")
else:
    isolados = sum(1 for tamanho in componentes if tamanho == 1)
    print(f"\nNos isolados (componentes de tamanho 1): {isolados}")
    print("Existem regioes que nao estao conectadas entre si.")
