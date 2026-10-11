from pathlib import Path
import json
import pandas as pd
from geometria_mapa import construir_linha

base = Path(__file__).resolve().parent
nos = pd.read_csv(base / "nos.csv")

coordenadas = {
    int(r.osmid): (float(r.latitude), float(r.longitude))
    for r in nos.itertuples(index=False)
}

with (base / "geometrias_osm.json").open(encoding="utf-8") as f:
    geometrias = json.load(f)

print("Geometrias cadastradas:", len(geometrias))

for registro in geometrias.values():
    a = int(registro["origem"])
    b = int(registro["destino"])

    for caminho in ([a, b], [b, a]):
        linha = construir_linha(caminho, coordenadas)
        inicio = coordenadas[caminho[0]]
        fim = coordenadas[caminho[-1]]

        assert len(linha) >= 2, f"Linha vazia: {caminho}"
        assert abs(linha[0][0] - inicio[0]) < 0.00002
        assert abs(linha[0][1] - inicio[1]) < 0.00002
        assert abs(linha[-1][0] - fim[0]) < 0.00002
        assert abs(linha[-1][1] - fim[1]) < 0.00002

        print(
            f"OK: {caminho[0]} -> {caminho[-1]} | "
            f"{len(linha)} pontos | orientação correta"
        )

print("Todos os testes passaram.")
