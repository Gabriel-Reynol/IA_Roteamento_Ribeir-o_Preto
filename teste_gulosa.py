
import pandas as pd

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from gulosa import busca_gulosa


TOLERANCIA = 15.0

TESTES = [
    (1827802528, 2191667380),
    (6384355656, 7562628474),
]


def validar_caminho(grafo, resultado, origem, destino):
    if resultado is None:
        return False

    caminho = resultado["caminho"]

    if not caminho:
        return False

    if caminho[0] != origem or caminho[-1] != destino:
        return False

    distancia_calculada = 0.0

    for a, b in zip(caminho, caminho[1:]):
        if a not in grafo or b not in grafo[a]:
            return False

        distancia_calculada += grafo[a][b]

    return abs(
        distancia_calculada - resultado["distancia"]
    ) < 0.01


def executar_teste(grafo, coordenadas, origem, destino, numero):
    print(f"\nTeste {numero:02d}")

    print(f"  Origem:  {origem}")
    print(f"  Destino: {destino}")

    # UCS fornece a distância ótima de referência.
    resultado_ucs = busca_custo_uniforme(
        grafo, origem, destino
    )

    # Executa a Busca Gulosa para a mesma rota.
    resultado_gulosa = busca_gulosa(
        grafo, coordenadas, origem, destino
    )

    if resultado_ucs is None:
        print("  Erro: UCS não encontrou uma rota.")
        print("  Resultado: FALHA")
        return

    if resultado_gulosa is None:
        print("  Erro: Busca Gulosa não encontrou uma rota.")
        print("  Resultado: FALHA")
        return

    distancia_otima = resultado_ucs["distancia"]
    distancia_gulosa = resultado_gulosa["distancia"]

    if distancia_otima > 0:
        excesso = (
            (distancia_gulosa - distancia_otima)
            / distancia_otima
        ) * 100
    else:
        excesso = 0.0

    expansoes_ucs = resultado_ucs["expandidos"]
    expansoes_gulosa = resultado_gulosa["expandidos"]

    valido = validar_caminho(
        grafo, resultado_gulosa, origem, destino
    )

    dentro_tolerancia = (
        distancia_gulosa <= distancia_otima * (1 + TOLERANCIA / 100)
    )

    print(
        f"  Distancia otima (UCS): "
        f"{distancia_otima:.2f} m"
    )

    print(
        f"  Distancia Gulosa:      "
        f"{distancia_gulosa:.2f} m"
    )

    print(f"  Excesso sobre o otimo: {excesso:.3f}%")

    print(f"  Expansoes UCS:         {expansoes_ucs}")
    print(f"  Expansoes Gulosa:      {expansoes_gulosa}")

    print(
        "  Validacao do caminho:  "
        + ("OK" if valido else "FALHA")
    )

    if valido and dentro_tolerancia:
        print("  Resultado: OK")
    else:
        print("  Resultado: FALHA")

    if valido and expansoes_ucs > 0:
        reducao = (
            (expansoes_ucs - expansoes_gulosa)
            / expansoes_ucs
        ) * 100

        print(
            f"  Reducao de expansoes:  {reducao:.2f}%"
        )


def main():
    print("Carregando mapa de Ribeirão Preto...")

    grafo = carregar_grafo()

    nos_df = pd.read_csv("nos.csv", index_col="osmid")

    coordenadas = {
        int(osmid): (linha.latitude, linha.longitude)
        for osmid, linha in nos_df.iterrows()
    }

    for numero, (origem, destino) in enumerate(TESTES, start=1):
        executar_teste(
            grafo, coordenadas, origem, destino, numero
        )


if __name__ == "__main__":
    main()
