import random
import sys
from pathlib import Path

DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
if str(DIRETORIO_PROJETO) not in sys.path:
    sys.path.insert(0, str(DIRETORIO_PROJETO))

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from weighted_astar import busca_weighted_a_estrela
import pandas as pd


def carregar_coordenadas():
    nos = pd.read_csv("nos.csv")
    return {
        int(linha["osmid"]): (
            float(linha["latitude"]),
            float(linha["longitude"])
        )
        for _, linha in nos.iterrows()
    }


def validar_caminho(grafo, resultado, origem, destino):
    if resultado is None:
        return False, "Nenhum caminho encontrado"

    caminho = resultado["caminho"]

    if not caminho or caminho[0] != origem or caminho[-1] != destino:
        return False, "Origem ou destino incorreto"

    distancia_calculada = 0.0

    for atual, proximo in zip(caminho, caminho[1:]):
        if proximo not in grafo.get(atual, {}):
            return False, f"Aresta inexistente: {atual} -> {proximo}"

        distancia_calculada += grafo[atual][proximo]

    if abs(distancia_calculada - resultado["distancia"]) > 0.01:
        return False, "Distancia retornada nao corresponde ao caminho"

    return True, "OK"


def main():
    grafo = carregar_grafo()
    coordenadas = carregar_coordenadas()
    nos = sorted(set(grafo) & set(coordenadas))

    # Amostra reproduzivel: a mesma semente gera os mesmos pares.
    random.seed(2026)
    amostra = random.sample(nos, min(20, len(nos)))

    pares = [
        (amostra[i], amostra[i + 1])
        for i in range(0, len(amostra) - 1, 2)
    ]

    total = 0
    falhas = 0
    total_exp_ucs = 0
    total_exp_weighted = 0
    pior_excesso = 0.0

    print(f"Nos disponiveis: {len(nos)}")
    print(f"Pares testados: {len(pares)}")
    print("-" * 110)

    for i, (origem, destino) in enumerate(pares, 1):
        otimo = busca_custo_uniforme(grafo, origem, destino)
        resultado = busca_weighted_a_estrela(
            grafo, coordenadas, origem, destino, peso=1.14
        )

        print(f"\nTeste {i:02d}")
        print(f"  Origem:  {origem}")
        print(f"  Destino: {destino}")

        if otimo is None or resultado is None:
            print("  FALHOU: caminho nao encontrado")
            falhas += 1
            continue

        caminho_ok, mensagem = validar_caminho(
            grafo, resultado, origem, destino
        )

        excesso = (
            resultado["distancia"] / otimo["distancia"] - 1
            if otimo["distancia"] > 0 else 0.0
        )
        excesso_pct = 100 * excesso
        pior_excesso = max(pior_excesso, excesso_pct)

        dentro_limite = excesso <= 0.15 + 1e-10
        passou = caminho_ok and dentro_limite

        if not passou:
            falhas += 1

        total += 1
        total_exp_ucs += otimo["expandidos"]
        total_exp_weighted += resultado["expandidos"]

        print(f"  Distancia otima (UCS): {otimo['distancia']:.2f} m")
        print(f"  Distancia Weighted A*: {resultado['distancia']:.2f} m")
        print(f"  Excesso sobre o otimo: {excesso_pct:.3f}%")
        print(f"  Expansoes UCS:         {otimo['expandidos']}")
        print(f"  Expansoes Weighted A*: {resultado['expandidos']}")
        print(f"  Validacao do caminho:  {mensagem}")
        print(f"  Resultado: {'OK' if passou else 'FALHOU'}")

        if not dentro_limite:
            print("  AVISO: a rota ultrapassou o limite de 15%.")

    print("\n" + "-" * 110)
    print(f"Testes concluidos: {total}")
    print(f"Falhas: {falhas}")
    print(f"Pior excesso observado: {pior_excesso:.3f}%")

    if total:
        reducao = (
            100 * (1 - total_exp_weighted / total_exp_ucs)
            if total_exp_ucs else 0
        )
        print(f"Expansoes UCS: {total_exp_ucs}")
        print(f"Expansoes Weighted A*: {total_exp_weighted}")
        print(f"Reducao agregada de expansoes: {reducao:.2f}%")

    if falhas == 0 and total > 0:
        print("RESULTADO: todos os pares passaram nos testes.")
    else:
        print("RESULTADO: investigar as falhas antes de integrar.")


if __name__ == "__main__":
    main()
