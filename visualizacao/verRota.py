from pathlib import Path
import folium
import pandas as pd
import json

# Diretorios do projeto e da visualizacao
DIRETORIO_PROJETO = Path(__file__).resolve().parent.parent
DIRETORIO_VISUALIZACAO = Path(__file__).resolve().parent

# 1. Carregar os nos e suas coordenadas
nos_df = pd.read_csv(
    DIRETORIO_PROJETO / "nos.csv",
    index_col="osmid"
)

# 2. Carregar a rota calculada
ARQUIVO_ROTA = DIRETORIO_VISUALIZACAO / "rota_ucs.json"

with open(ARQUIVO_ROTA, "r", encoding="utf-8") as arquivo:
    caminho_ids = json.load(arquivo)

# 3. Extrair as coordenadas da rota
caminho_coordenadas = []

for no_id in caminho_ids:
    if no_id in nos_df.index:
        lat = nos_df.loc[no_id, "latitude"]
        lon = nos_df.loc[no_id, "longitude"]
        caminho_coordenadas.append((lat, lon))

# Evitar erro se nenhum no da rota for encontrado
if not caminho_coordenadas:
    raise ValueError(
        "Nenhum no da rota foi encontrado em nos.csv. "
        "Confira os IDs em rota_ucs.json."
    )

# 4. Criar o mapa
mapa = folium.Map(
    location=caminho_coordenadas[0],
    zoom_start=14,
    tiles="OpenStreetMap"
)

# 5. Desenhar a rota
folium.PolyLine(
    locations=caminho_coordenadas,
    color="red",
    weight=5,
    opacity=0.8
).add_to(mapa)

# 6. Marcar origem e destino
folium.Marker(
    caminho_coordenadas[0],
    popup="Origem",
    icon=folium.Icon(color="green")
).add_to(mapa)

folium.Marker(
    caminho_coordenadas[-1],
    popup="Destino",
    icon=folium.Icon(color="red")
).add_to(mapa)

# 7. Salvar o mapa na pasta visualizacao
ARQUIVO_SAIDA = DIRETORIO_VISUALIZACAO / "rotaBuscaGrupoX.html"
mapa.save(str(ARQUIVO_SAIDA))

print(f"Mapa de rota gerado com sucesso: {ARQUIVO_SAIDA}")
