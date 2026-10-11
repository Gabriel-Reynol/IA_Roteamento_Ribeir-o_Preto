import json
from pathlib import Path


BASE = Path(__file__).resolve().parent
ARQUIVO_GEOMETRIAS = BASE / "geometrias_osm.json"


def carregar_geometrias():
    if not ARQUIVO_GEOMETRIAS.exists():
        return {}

    try:
        with ARQUIVO_GEOMETRIAS.open("r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return dados if isinstance(dados, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def construir_linha(caminho, coordenadas):
    """Monta uma linha contínua, usando geometrias OSM quando validadas."""
    geometrias = carregar_geometrias()
    linha = []

    for a, b in zip(caminho, caminho[1:]):
        a, b = int(a), int(b)

        if a not in coordenadas or b not in coordenadas:
            continue

        inicio = coordenadas[a]
        fim = coordenadas[b]
        registro = geometrias.get(f"{a}|{b}")
        invertida = False

        if registro is None:
            registro = geometrias.get(f"{b}|{a}")
            invertida = registro is not None

        segmento = None
        if registro and registro.get("validada") is True:
            pontos = registro.get("coordenadas_lat_lon", [])
            if len(pontos) >= 2:
                segmento = [(float(p[0]), float(p[1])) for p in pontos]
                if invertida:
                    segmento.reverse()

                # Só usa a geometria se ela realmente conecta os nós esperados.
                def perto(p, q):
                    return abs(p[0] - q[0]) < 0.00002 and abs(p[1] - q[1]) < 0.00002

                if not (perto(segmento[0], inicio) and perto(segmento[-1], fim)):
                    segmento = None

        if segmento is None:
            segmento = [inicio, fim]

        if not linha:
            linha.extend(segmento)
        else:
            # Evita repetir o primeiro ponto de cada segmento.
            if linha[-1] == segmento[0]:
                linha.extend(segmento[1:])
            else:
                linha.extend(segmento)

    return linha
