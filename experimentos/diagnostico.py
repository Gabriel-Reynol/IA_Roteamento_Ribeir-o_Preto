import pandas as pd
from math import radians, sin, cos, asin, sqrt

nos = pd.read_csv("nos.csv")
arestas = pd.read_csv("arestas.csv")

print("=== ESTRUTURA DOS DADOS ===")
print("Nós:", len(nos))
print("Arestas:", len(arestas))
print("Colunas dos nós:", list(nos.columns))
print("Colunas das arestas:", list(arestas.columns))
print("IDs de nós duplicados:", nos["osmid"].duplicated().sum())
print("Coordenadas ausentes:", nos[["latitude", "longitude"]].isna().any(axis=1).sum())
print("Distâncias ausentes:", arestas["distancia"].isna().sum())
print("Distâncias não positivas:", (arestas["distancia"] <= 0).sum())

coords = nos.set_index("osmid")[["latitude", "longitude"]].to_dict("index")
ids = set(coords)

faltantes = (set(arestas["origem"]) | set(arestas["destino"])) - ids
print("Nós sem coordenadas:", len(faltantes))

def haversine(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
    return 2 * 6371000 * asin(sqrt(min(1, a)))

violacoes = []
for r in arestas.itertuples(index=False):
    if r.origem not in ids or r.destino not in ids or pd.isna(r.distancia):
        continue
    a, b = coords[r.origem], coords[r.destino]
    reta = haversine(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
    if r.distancia + 1 < reta:
        violacoes.append((r.origem, r.destino, round(r.distancia, 2), round(reta, 2)))

print("Arestas abaixo da distância em linha reta:", len(violacoes))
print("Exemplos:", violacoes[:10])
