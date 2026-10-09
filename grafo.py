
import pandas as pd

def carregar_grafo():

    arestas = pd.read_csv("arestas.csv")
    grafo = {}

    for _, linha in arestas.iterrows():
        origem = int(linha["origem"])
        destino = int(linha["destino"])
        distancia = float(linha["distancia"])

        if origem not in grafo:
            grafo[origem] = {}

        if destino not in grafo:
            grafo[destino] = {}

        if destino not in grafo[origem] or distancia < grafo[origem][destino]:
            grafo[origem][destino] = distancia
            grafo[destino][origem] = distancia

    return grafo
