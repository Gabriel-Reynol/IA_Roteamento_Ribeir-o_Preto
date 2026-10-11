import csv
import json
import requests
import xml.etree.ElementTree as ET
from math import radians, sin, cos, asin, sqrt
from pathlib import Path

BASE = Path(__file__).resolve().parent
ARQUIVO_ARESTAS = BASE / "arestas.csv"
ARQUIVO_SAIDA = BASE / "geometrias_osm.json"

PARES = [
    ("259576101", "2007042255", "190096080"),
    ("2023807944", "259576101", "191812143"),
]

TOLERANCIA_METROS = 2.0

sessao = requests.Session()
sessao.headers.update({
    "User-Agent": "IA-Roteamento-Ribeirao-Preto/1.0"
})

def distancia_m(a, b):
    lat1, lon1 = map(radians, a)
    lat2, lon2 = map(radians, b)
    dlat, dlon = lat2-lat1, lon2-lon1
    h = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    return 6371000 * 2 * asin(sqrt(h))

with ARQUIVO_ARESTAS.open(encoding="utf-8-sig", newline="") as f:
    arestas = list(csv.DictReader(f))

if ARQUIVO_SAIDA.exists():
    with ARQUIVO_SAIDA.open("r", encoding="utf-8") as f:
        resultado = json.load(f)
    if not isinstance(resultado, dict):
        raise ValueError(
            "O arquivo de geometrias existente nao contem um objeto JSON."
        )
else:
    resultado = {}
for origem, destino, via_id in PARES:
    registros = [
        a for a in arestas
        if {a["origem"], a["destino"]} == {origem, destino}
    ]

    if not registros:
        raise RuntimeError(f"Aresta ausente no CSV: {origem} - {destino}")

    peso = float(registros[0]["distancia"])

    url = f"https://api.openstreetmap.org/api/0.6/way/{via_id}/full"
    r = sessao.get(url, timeout=30)
    r.raise_for_status()
    raiz = ET.fromstring(r.content)

    via = raiz.find("way")
    refs = [n.attrib["ref"] for n in via.findall("nd")]
    coords = {
        n.attrib["id"]: [
            float(n.attrib["lat"]),
            float(n.attrib["lon"])
        ]
        for n in raiz.findall("node")
    }

    if origem not in refs or destino not in refs:
        raise RuntimeError(
            f"Extremos não encontrados na via {via_id}: "
            f"{origem} -> {destino}"
        )

    candidatos = []

    for i, no_origem in enumerate(refs):
        if no_origem != origem:
            continue

        for j, no_destino in enumerate(refs):
            if no_destino != destino or i == j:
                continue

            passo = 1 if j > i else -1
            trecho_refs = refs[i:j + passo:passo]

            if not all(n in coords for n in trecho_refs):
                continue

            pontos_candidato = [coords[n] for n in trecho_refs]
            comprimento_candidato = sum(
                distancia_m(
                    pontos_candidato[k],
                    pontos_candidato[k + 1]
                )
                for k in range(len(pontos_candidato) - 1)
            )

            diferenca_candidata = abs(comprimento_candidato - peso)
            candidatos.append((
                diferenca_candidata,
                trecho_refs,
                pontos_candidato,
                comprimento_candidato
            ))

    if not candidatos:
        raise RuntimeError(
            f"Nenhum trecho valido encontrado na via {via_id}: "
            f"{origem} -> {destino}"
        )

    diferenca, trecho_refs, pontos, comprimento = min(
        candidatos, key=lambda item: item[0]
    )

    diferenca = abs(comprimento - peso)

    print(f"\nAresta {origem} -> {destino}")
    print(f"  Via OSM: {via_id}")
    print(f"  Peso original: {peso:.2f} m")
    print(f"  Geometria: {comprimento:.2f} m")
    print(f"  Diferença: {diferenca:.2f} m")

    if diferenca > TOLERANCIA_METROS:
        raise RuntimeError(
            "Validação reprovada. Nenhum arquivo de saída foi salvo."
        )

    chave = f"{origem}|{destino}"
    resultado[chave] = {
        "origem": origem,
        "destino": destino,
        "via_osm": via_id,
        "distancia_original_m": peso,
        "distancia_geometrica_m": round(comprimento, 3),
        "coordenadas_lat_lon": pontos,
        "validada": True
    }

tmp = ARQUIVO_SAIDA.with_suffix(".tmp")
tmp.write_text(
    json.dumps(resultado, ensure_ascii=False, indent=2),
    encoding="utf-8"
)
tmp.replace(ARQUIVO_SAIDA)

print(f"\nArquivo auxiliar criado: {ARQUIVO_SAIDA}")
print("CSV e algoritmos permaneceram intactos.")
