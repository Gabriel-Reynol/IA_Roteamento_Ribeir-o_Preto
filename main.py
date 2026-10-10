import json
import pandas as pd

from grafo import carregar_grafo
from ucs import busca_custo_uniforme
from A_estrela import busca_a_estrela
from weighted_astar import busca_weighted_a_estrela


def mostrar_resultado(nome, resultado, origem, destino):
    if resultado is None:
        print(f"\nNenhuma rota encontrada com {nome}.")
        return

    print(f"\nRESULTADO DA BUSCA - {nome}")
    print("Algoritmo utilizado:", nome)
    print("Origem:", origem)
    print("Destino:", destino)
    print("Caminho:", resultado["caminho"])
    print("Quantidade de nós:", len(resultado["caminho"]))
    print(f"Distância: {resultado['distancia']:.2f} metros")
    print("Nós expandidos:", resultado["expandidos"])


def salvar_rota(nome_arquivo, resultado):
    if resultado is not None:
        with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
            json.dump(resultado["caminho"], arquivo)
        print(f"Caminho salvo em {nome_arquivo}")


def percentual_reducao(referencia, resultado):
    if referencia <= 0:
        return 0.0
    return (referencia - resultado) / referencia * 100


def executar_busca(grafo, coordenadas, origem, destino, opcao):
    if opcao == "1":
        resultado = busca_custo_uniforme(grafo, origem, destino)
        mostrar_resultado("UCS (Referência ótima)", resultado, origem, destino)
        salvar_rota("rota_ucs.json", resultado)

    elif opcao == "2":
        resultado = busca_a_estrela(grafo, coordenadas, origem, destino)
        mostrar_resultado("A* (Desafio 1 - rota ótima)", resultado, origem, destino)
        salvar_rota("rota_astar.json", resultado)

    elif opcao == "3":
        referencia = busca_custo_uniforme(grafo, origem, destino)
        resultado = busca_weighted_a_estrela(
            grafo, coordenadas, origem, destino, peso=1.14
        )

        if referencia is None or resultado is None:
            print("\nNão foi possível encontrar uma rota.")
            return

        if referencia["distancia"] > 0:
            excesso = (
                (resultado["distancia"] - referencia["distancia"])
                / referencia["distancia"] * 100
            )
        else:
            excesso = 0.0

        reducao = percentual_reducao(
            referencia["expandidos"], resultado["expandidos"]
        )

        print("\nCOMPARAÇÃO DO DESAFIO 2")
        print(f"Distância ótima (UCS): {referencia['distancia']:.2f} m")
        print(f"Distância Weighted A*: {resultado['distancia']:.2f} m")
        print(f"Excesso em relação ao ótimo: {excesso:.2f}%")
        print(f"Expansões UCS: {referencia['expandidos']}")
        print(f"Expansões Weighted A*: {resultado['expandidos']}")
        print(f"Redução de expansões: {reducao:.2f}%")

        if excesso > 15.0:
            print("\nATENÇÃO: a rota Weighted A* ultrapassou 15% de excesso.")
            print("Será utilizada a rota ótima do UCS como alternativa.")
            resultado_final = referencia
            nome_rota = "UCS (alternativa dentro do limite)"
        else:
            resultado_final = resultado
            nome_rota = "Weighted A* (Desafio 2)"

        mostrar_resultado(nome_rota, resultado_final, origem, destino)
        salvar_rota("rota_desafio2.json", resultado_final)

    elif opcao == "4":
        ucs = busca_custo_uniforme(grafo, origem, destino)
        astar = busca_a_estrela(grafo, coordenadas, origem, destino)

        mostrar_resultado("UCS (Referência)", ucs, origem, destino)
        mostrar_resultado("A* (Desafio 1)", astar, origem, destino)

        salvar_rota("rota_ucs.json", ucs)
        salvar_rota("rota_astar.json", astar)

        if ucs is not None and astar is not None:
            print("\nCOMPARAÇÃO UCS x A*")
            reducao = percentual_reducao(
                ucs["expandidos"], astar["expandidos"]
            )
            print(f"Distância UCS: {ucs['distancia']:.2f} m")
            print(f"Distância A*: {astar['distancia']:.2f} m")
            print(f"Expansões UCS: {ucs['expandidos']}")
            print(f"Expansões A*: {astar['expandidos']}")
            print(f"Redução de expansões: {reducao:.2f}%")


def main():
    print("Carregando mapa de Ribeirão Preto...")
    grafo = carregar_grafo()
    nos_df = pd.read_csv("nos.csv", index_col="osmid")

    coordenadas = {
        int(osmid): (linha.latitude, linha.longitude)
        for osmid, linha in nos_df.iterrows()
    }

    print("\nSISTEMA DE ROTEAMENTO - RIBEIRÃO PRETO")
    print("Total de nós:", len(grafo))

    while True:
        print("\n--------------------------------------")

        try:
            origem = int(input("Digite o OSMID de origem: "))
            destino = int(input("Digite o OSMID de destino: "))
        except ValueError:
            print("Erro: digite identificadores numéricos.")
            continue

        if origem not in grafo or destino not in grafo:
            print("Erro: origem ou destino não encontrado no mapa.")
            continue

        print("\nEscolha o algoritmo:")
        print("1 - UCS (Referência ótima)")
        print("2 - A* (Desafio 1 - rota ótima)")
        print("3 - Weighted A* (Desafio 2 - limite de 15%)")
        print("4 - Comparar UCS e A*")

        opcao = input("\nOpção: ").strip()

        if opcao in ("1", "2", "3", "4"):
            executar_busca(grafo, coordenadas, origem, destino, opcao)
        else:
            print("Opção inválida.")

        while True:
            continuar = input(
                "\nDeseja testar outra busca ou destino? (S/N): "
            ).strip().upper()

            if continuar in ("S", "N"):
                break

            print("Digite S para sim ou N para não.")

        if continuar == "N":
            print("\nObrigado por utilizar o Sistema de Roteamento!")
            break


if __name__ == "__main__":
    main()
