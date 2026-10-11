# IA para Roteamento em Ribeirão Preto

Projeto acadêmico de busca em grafos para planejamento e comparação de rotas em Ribeirão Preto, com visualização geográfica.

## Funcionalidades

- Busca de Custo Uniforme (UCS).
- Busca A*.
- Weighted A*.
- Busca Gulosa.
- Beam Search.
- Comparação experimental entre algoritmos.
- Visualização de rotas em mapas.
- Uso de geometrias viárias para representar trechos das rotas com maior fidelidade.

## Tecnologias

- Python
- Pandas
- Streamlit
- Folium
- Plotly
- PySide6
- Matplotlib
- Requests

## Estrutura do projeto

| Arquivo ou diretório | Finalidade |
|---|---|
| `main.py` | Entrada da aplicação principal e seleção de algoritmos |
| `app.py` | Interface web com Streamlit |
| `desktop_app.py` | Interface desktop |
| `grafo.py` | Estrutura e operações do grafo |
| `ucs.py` | Busca de Custo Uniforme |
| `A_estrela.py` | Busca A* |
| `weighted_astar.py` | Busca Weighted A* |
| `busca_gulosa.py` e `gulosa.py` | Implementações relacionadas à Busca Gulosa |
| `beam_search.py` | Busca Beam Search |
| `nos.csv` | Dados dos nós do grafo |
| `arestas.csv` | Dados das arestas do grafo |
| `geometria_mapa.py` | Construção das linhas geográficas das rotas |
| `geometrias_osm.json` | Geometrias viárias armazenadas em JSON |
| `gerar_geometrias_osm.py` | Script para obter e validar geometrias viárias |
| `testes/` | Scripts de validação |
| `experimentos/` | Scripts de análise e comparação de algoritmos |
| `visualizacao/` | Recursos de visualização |

## Requisitos

- Python compatível com as versões das dependências utilizadas.
- Git, para clonar o repositório.
- Conexão com a internet para instalar dependências e, quando necessário, consultar serviços externos.

## Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/Gabriel-Reynol/IA_Roteamento_Ribeir-o_Preto.git
cd IA_Roteamento_Ribeir-o_Preto
```

Crie e ative um ambiente virtual.

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

## Execução

Interface web:

```powershell
streamlit run app.py
```

Interface desktop:

```powershell
python desktop_app.py
```

Entrada principal:

```powershell
python main.py
```

A disponibilidade de cada modo de execução depende das funcionalidades implementadas no respectivo arquivo.

## Testes e validações

Execute os scripts de validação a partir da raiz do projeto:

```powershell
python testar_geometria_mapa.py
python testes/teste_conectividade.py
python testes/teste_limites.py
python testes/validar_rotas.py
```

Esses scripts verificam aspectos da geometria, conectividade e comportamento das rotas. Os resultados dependem dos dados e da versão atual do projeto.

## Dados geográficos

O projeto utiliza arquivos CSV para representar nós e arestas do grafo. O módulo `geometria_mapa.py` complementa as coordenadas dos nós com geometrias viárias validadas quando disponíveis, recorrendo ao segmento entre os nós quando não há geometria utilizável.

O script `gerar_geometrias_osm.py` destina-se à obtenção de geometrias de vias. Sua execução pode consultar serviços externos e atualizar o arquivo de geometrias; revise seu comportamento e os dados antes de executá-lo.

## Estado do projeto

Projeto em desenvolvimento. Resultados experimentais e funcionalidades devem ser interpretados conforme os dados, parâmetros e testes utilizados em cada versão.

## Licença

Nenhuma licença foi especificada neste repositório até o momento.
