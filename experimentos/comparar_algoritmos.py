import random
from time import perf_counter
from pathlib import Path
import pandas as pd

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent

import sys
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela
from weighted_astar import busca_weighted_a_estrela
from busca_gulosa import busca_gulosa
from beam_search import busca_beam


def carregar_coordenadas():
    nos = pd.read_csv(DIRETORIO_PROJETO / "nos.csv")
    return {
        int(linha["osmid"]): (
            float(linha["latitude"]),
            float(linha["longitude"])
        )
        for _, linha in nos.iterrows()
    }


def validar_caminho(grafo, resultado, origem, destino):
    if resultado is None:
        return False

    caminho = resultado["caminho"]

    if not caminho or caminho[0] != origem or caminho[-1] != destino:
        return False

    distancia = 0.0

    for a, b in zip(caminho, caminho[1:]):
        if b not in grafo.get(a, {}):
            return False
        distancia += grafo[a][b]

    return abs(distancia - resultado["distancia"]) <= 0.01


def executar(funcao, *args):
    inicio = perf_counter()
    resultado = funcao(*args)
    tempo = perf_counter() - inicio
    return resultado, tempo


def main():
    grafo = carregar_grafo()
    coordenadas = carregar_coordenadas()
    nos = sorted(set(grafo) & set(coordenadas))

    random.seed(2026)
    amostra = random.sample(nos, min(200, len(nos)))
    pares = [
        (amostra[i], amostra[i + 1])
        for i in range(0, len(amostra) - 1, 2)
    ]

    algoritmos = {
        "UCS": lambda o, d: busca_custo_uniforme(grafo, o, d),
        "A*": lambda o, d: busca_a_estrela(
            grafo, coordenadas, o, d
        ),
        "Weighted A*": lambda o, d: busca_weighted_a_estrela(
            grafo, coordenadas, o, d, peso=1.14
        ),
        "Beam k=10": lambda o, d: busca_beam(grafo, coordenadas, o, d, largura=10),
        "Beam k=25": lambda o, d: busca_beam(grafo, coordenadas, o, d, largura=25),
        "Beam k=50": lambda o, d: busca_beam(grafo, coordenadas, o, d, largura=50),
        "Beam k=100": lambda o, d: busca_beam(grafo, coordenadas, o, d, largura=100),
        "Gulosa": lambda o, d: busca_gulosa(
            grafo, coordenadas, o, d
        )
    }

    totais = {
        nome: {"expandidos": 0, "tempo": 0.0, "falhas": 0,
               "excessos": []}
        for nome in algoritmos
    }

    print(f"Nos disponiveis: {len(nos)}")
    print(f"Pares testados: {len(pares)}")
    print("A rota otima de referencia e calculada pelo UCS.")
    print("=" * 100)

    for i, (origem, destino) in enumerate(pares, 1):
        resultados = {}
        tempos = {}

        print(f"\nTESTE {i:02d} | Origem: {origem} | Destino: {destino}")

        for nome, funcao in algoritmos.items():
            resultado, tempo = executar(funcao, origem, destino)
            resultados[nome] = resultado
            tempos[nome] = tempo

            totais[nome]["tempo"] += tempo

        otimo = resultados["UCS"]

        if otimo is None or otimo["distancia"] <= 0:
            print("Nao foi possivel estabelecer a distancia otima.")
            for nome in algoritmos:
                totais[nome]["falhas"] += 1
            continue

        distancia_otima = otimo["distancia"]

        for nome in algoritmos:
            resultado = resultados[nome]
            dados = totais[nome]

            if resultado is None or not validar_caminho(
                grafo, resultado, origem, destino
            ):
                dados["falhas"] += 1
                print(f"  {nome:13} | Rota invalida ou nao encontrada")
                continue

            excesso = (
                resultado["distancia"] / distancia_otima - 1
            ) * 100

            dados["expandidos"] += resultado["expandidos"]
            dados["excessos"].append(excesso)

            limite_ok = excesso <= 15.0 + 1e-8
            dados["fora_limite"] = dados.get("fora_limite", 0)
            if not limite_ok:
                dados["fora_limite"] += 1

            status = "OK" if limite_ok else "ACIMA DE 15%"

            print(
                f"  {nome:13} | "
                f"dist={resultado['distancia']:10.2f} m | "
                f"excesso={excesso:7.3f}% | "
                f"exp={resultado['expandidos']:6d} | "
                f"tempo={tempos[nome] * 1000:8.3f} ms | {status}"
            )

    print("\n" + "=" * 100)
    print("RESUMO AGREGADO")
    print("-" * 100)

    exp_ucs = totais["UCS"]["expandidos"]

    for nome, dados in totais.items():
        excessos = dados["excessos"]
        media_excesso = (
            sum(excessos) / len(excessos) if excessos else float("nan")
        )
        pior_excesso = max(excessos) if excessos else float("nan")
        reducao = (
            (1 - dados["expandidos"] / exp_ucs) * 100
            if exp_ucs and nome != "UCS" else 0.0
        )

        fora = dados.get("fora_limite", 0)

        print(f"\n{nome}")
        print(f"  Expansoes totais: {dados['expandidos']}")
        print(f"  Tempo total: {dados['tempo']:.4f} s")
        print(f"  Reducao de expansoes vs UCS: {reducao:.2f}%")
        print(f"  Excesso medio sobre UCS: {media_excesso:.3f}%")
        print(f"  Pior excesso: {pior_excesso:.3f}%")
        print(f"  Rotas acima de 15%: {fora}")
        print(f"  Falhas de validacao: {dados['falhas']}")

    print("\nObservacao: os tempos variam com a carga do computador.")
    print("A Busca Gulosa nao garante o limite de 15%.")


if __name__ == "__main__":
    main()
