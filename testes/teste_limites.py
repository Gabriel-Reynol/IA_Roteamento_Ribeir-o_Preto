import sys
from pathlib import Path

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))
import pandas as pd
from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela

grafo = carregar_grafo()
nos = pd.read_csv("nos.csv")
coordenadas = {
    int(row.osmid): (row.latitude, row.longitude)
    for row in nos.itertuples(index=False)
}

origem = next(iter(grafo))

print(f"No escolhido: {origem}")
print("\n=== UCS: origem igual ao destino ===")
print(busca_custo_uniforme(grafo, origem, origem))

print("\n=== A*: origem igual ao destino ===")
print(busca_a_estrela(grafo, coordenadas, origem, origem))
