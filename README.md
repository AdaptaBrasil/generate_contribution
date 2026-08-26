# generate_contribution

[![GitHub](https://img.shields.io/badge/GitHub-generate__contribution-blue?logo=github)](https://github.com/AdaptaBrasil/generate_contribution)
[![CI](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml/badge.svg)](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml)
[![Python 3.11 | 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](https://github.com/AdaptaBrasil/generate_contribution/blob/master/.github/workflows/ci.yml)

Pipeline de tratamento e geração de relatórios de indicadores do AdaptaBrasil: winsorização,
Box-Cox, normalização, diagnósticos de correlação/VIF/alfa de Cronbach, e um relatório em
PowerPoint (com mapas por indicador e um diagrama setorial).

## Primeiros passos

### O que ele faz

`generate_contribution` transforma uma planilha bruta de indicadores do AdaptaBrasil em um
conjunto de dados validado e pronto para relatório, em três etapas:

1. **Tratamento** — winsoriza outliers, aplica uma transformação Box-Cox condicionada por
   assimetria/curtose, e normaliza cada indicador por min-max, gravando duas planilhas Excel (um
   resumo de estatísticas descritivas e os dados tratados em cada etapa).
2. **Diagnósticos** — correlação de Spearman/parcial, VIF, e alfa de Cronbach (com reversão
   automática de itens invertidos), além dos quatro gráficos PNG de diagnóstico (contagem de NAs,
   dois correlogramas, VIF, impacto no alfa).
3. **Relatório** — um documento PowerPoint com um grupo de slides por indicador (tabela descritiva
   + boxplot/histograma + mapa coroplético, em cada uma das etapas bruta/winsorizada/Box-Cox/
   normalizada), além de um slide com o diagrama setorial.

A etapa 1 sempre é executada; as etapas 2 e 3 são opcionais (`--no-diagnostics`/`--no-report` no
comando `pipeline`, veja abaixo).

### 1. Obter os arquivos

```
git clone https://github.com/AdaptaBrasil/generate_contribution.git
cd generate_contribution
```

O conjunto de dados de exemplo, os shapefiles e o template PPTX necessários para executar o
pipeline já estão incluídos em `DATASET/`/`TEMPLATE/` (veja "Ativos de dados" abaixo) — não é
preciso baixar nada além disso para testar.

### 2. Criar um ambiente virtual

macOS/Linux:

```
python3 -m venv .venv
source .venv/bin/activate
```

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Instalar o pacote e suas dependências

```
pip install -e ".[dev]"
```

Isso instala a biblioteca, a CLI `generate-contribution`, e tudo que está em
`[project.dependencies]` no `pyproject.toml` (pandas, numpy, scipy, geopandas, python-pptx, etc.);
`[dev]` adicionalmente traz o `pytest` para rodar a suíte de testes. Omita `[dev]` se você só
precisa executar o pipeline.

A etapa de diagrama (`generate_contribution.diagrams`) requer adicionalmente uma instalação do
**Graphviz** no sistema (o executável `dot` no PATH) — por exemplo `winget install
Graphviz.Graphviz` no Windows, `apt install graphviz` / `dnf install graphviz` no Linux.

### 4. Parâmetros

A CLI tem dois subcomandos. `generate-contribution tratamento` executa apenas a etapa 1:

| Flag | Obrigatório | Padrão | Significado |
|---|---|---|---|
| `--input` | sim | — | Caminho da planilha `.xlsx` de entrada. |
| `--imeta-sheet` | não | `Metadados` | Nome da planilha com os metadados dos indicadores (colunas `Nivel`/`Code`/`Nome`/`Pai`/`Classe`). |
| `--idata-sheet` | sim | — | Nome da planilha com os dados brutos (`GEOCOD`/`MUN`/`UF`/`CLUSTER` + uma coluna por indicador). |
| `--method-boxcox` | não | `forecast` | Mecanismo do Box-Cox: `forecast` (lambda por MLE) ou `yeojohnson`. |
| `--sigla` | não | `SE` | Código curto usado nos nomes dos arquivos de saída (ex.: `SA`). |
| `--subsetor` | não | — | Anexado ao `--sigla` nos nomes dos arquivos e nos títulos do relatório (ex.: `ACESSO`). |
| `--output-dir` | não | `OUTPUT` | Diretório onde os dois arquivos `.xlsx` de saída são gravados. |

`generate-contribution pipeline` executa as três etapas e aceita todas as flags acima, além de:

| Flag | Obrigatório | Padrão | Significado |
|---|---|---|---|
| `--template` | sim | — | Caminho do template PPTX (ex.: `TEMPLATE/ADAPTA_RESUMO.pptx`). |
| `--setor-estrategico` | sim | — | Nome do setor exibido no slide de título do relatório. |
| `--shp-mun` | sim | — | Shapefile dos limites municipais (`.shp`). |
| `--shp-uf` | sim | — | Shapefile dos limites estaduais (`.shp`). |
| `--ind` | não | todos | Limita o relatório aos N primeiros indicadores — útil para um teste rápido antes de gerar o documento completo. |
| `--figs-dir` | não | `FIGs` | Diretório onde os PNGs de diagnóstico são gravados. |
| `--no-report` | não | desligado | Pula a geração do PPTX (apenas tratamento + diagnósticos). |
| `--no-diagnostics` | não | desligado | Pula os diagnósticos de correlação/VIF/Cronbach e as figuras. |

Veja a seção "CLI" abaixo para exemplos completos de invocação.

## Referência dos módulos

| Módulo Python | Responsabilidade |
|---|---|
| `cli.py`, `pipeline.py` | Pontos de entrada da CLI e orquestração de alto nível do pipeline |
| `resumo.py` | Estatísticas descritivas (estatísticas de boxplot, resumos por indicador/por cluster) |
| `winsorise.py` | Winsorização (corte de outliers) |
| `boxcox.py` | Transformação Box-Cox condicionada por assimetria/curtose |
| `normalise.py` | Normalização min-max |
| `treatment.py`, `io_excel.py` | Orquestração do tratamento de ponta a ponta + I/O de Excel |
| `correlation.py` | Diagnósticos de correlação/VIF/alfa de Cronbach |
| `figures.py` | Gráficos PNG de diagnóstico e por indicador |
| `maps.py` | Mapas coropléticos |
| `diagrams.py` | Diagrama setorial |
| `pptx_report.py` | Montagem do relatório PowerPoint |

## Ativos de dados

`DATASET/` e `TEMPLATE/` contêm ativos reais, prontos para uso, de modo que este projeto funciona
de forma autônoma:

- `DATASET/Base_inicial_SA_Acesso.xlsx` — planilha de entrada de exemplo (planilhas `Metadados` +
  `Dados_RA_Acesso`).
- `DATASET/Base_inicial_RH_INDBRT.xlsx` — uma segunda planilha de exemplo (planilhas `Metadados` +
  `Dados_RH_INDBRT`); a coluna de indicador-pai de seus metadados foi renomeada de `Parente` para
  `Pai` na importação, para corresponder ao esquema esperado por `diagrams.py`/`resumo.py`. Inclui
  um indicador classificado como `Cluster`, então executar o relatório PPTX com ela atualmente
  esbarra na limitação de Cluster descrita abaixo — o tratamento e os diagnósticos funcionam
  normalmente.
- `DATASET/SHP/BR_Municipios_2022_gr.*`, `DATASET/SHP/BR_UF_2022_gr.*` — shapefiles dos limites
  municipais/estaduais usados por `maps.py`.
- `TEMPLATE/ADAPTA_RESUMO.pptx` — template PPTX usado por `pptx_report.py`.
- `DESCRITORES/DESCRITORES.xlsx`, `DESCRITORES/DIGRAMA_RH.pdf` — documentos de referência para
  consulta humana, não lidos por nenhum código.

## CLI

```
# Apenas tratamento (winsorização/Box-Cox/normalização + as duas planilhas de saída)
generate-contribution tratamento \
  --input DATASET/Base_inicial_SA_Acesso.xlsx --idata-sheet Dados_RA_Acesso \
  --sigla SA --subsetor ACESSO --output-dir OUTPUT

# Pipeline completo: tratamento -> relatório PPTX -> diagnósticos de correlação/VIF/Cronbach + figuras
generate-contribution pipeline \
  --input DATASET/Base_inicial_SA_Acesso.xlsx --idata-sheet Dados_RA_Acesso \
  --sigla SA --subsetor ACESSO \
  --template TEMPLATE/ADAPTA_RESUMO.pptx --setor-estrategico "Segurança Alimentar" \
  --shp-mun DATASET/SHP/BR_Municipios_2022_gr.shp --shp-uf DATASET/SHP/BR_UF_2022_gr.shp \
  --output-dir OUTPUT --figs-dir FIGs
```

## Notebook de exemplo (Jupyter)

`jupyter_example.ipynb` (e seu equivalente sem Jupyter, `plain_python_example.py`) executam o
pipeline completo chamando `run_pipeline` diretamente em Python, como alternativa à CLI.

Para rodar: abra `jupyter_example.ipynb`, ajuste `tratamento_config`/`report_config` (veja abaixo)
e use **Run All** para executar tudo de uma vez, ou execute célula por célula com Shift+Enter — a
única dependência entre células é a ordem (`BASE_DIR` precisa existir antes das duas células de
configuração, que por sua vez precisam existir antes da célula que chama `run_pipeline`).

### O que ajustar em `tratamento_config` (`TratamentoConfig`)

| Campo | Obrigatório | Significado |
|---|---|---|
| `input` | sim | Caminho da planilha `.xlsx` de entrada, ex.: `BASE_DIR / "DATASET" / "Base_inicial_SA_Acesso.xlsx"`. |
| `imeta_sheet` | não (padrão `"Metadados"`) | Nome da planilha com os metadados dos indicadores. |
| `idata_sheet` | sim | Nome da planilha com os dados brutos (`GEOCOD`/`MUN`/`UF`/`CLUSTER` + uma coluna por indicador). |
| `method_boxcox` | não (padrão `"forecast"`) | Mecanismo do Box-Cox: `"forecast"` (lambda por MLE) ou `"yeojohnson"`. |
| `sigla` | não (padrão `"SE"`) | Código curto usado nos nomes dos arquivos de saída (ex.: `"SA"`). |
| `subsetor` | não | Anexado à `sigla` nos nomes dos arquivos e nos títulos do relatório (ex.: `"ACESSO"`). |
| `output_dir` | não (padrão `"OUTPUT"`) | Diretório onde os arquivos de saída são gravados. |

### O que ajustar em `report_config` (`ReportConfig`)

| Campo | Obrigatório | Significado |
|---|---|---|
| `template` | sim | Caminho do template PPTX, ex.: `BASE_DIR / "TEMPLATE" / "ADAPTA_RESUMO.pptx"`. |
| `setor_estrategico` | sim | Nome do setor exibido no slide de título do relatório. |
| `sigla` / `subsetor` | sim / não | Mesmo significado de `tratamento_config`; normalmente repetidos com os mesmos valores. |
| `caminho_shp_mun` / `caminho_shp_uf` | sim | Shapefiles dos limites municipais/estaduais (`.shp`). |
| `ind` | não (padrão todos) | Limita o relatório aos N primeiros indicadores — útil para um teste rápido. |
| `resu`, `winz`, `bxcx`, `norm` | não (padrão `True`) | Liga/desliga os grupos de slides de cada etapa (descritivo/winsorizado/Box-Cox/normalizado). |
| `output_dir` | não (padrão `"OUTPUT"`) | Deve apontar para o mesmo diretório usado em `tratamento_config.output_dir`. |

A célula `run_pipeline(...)` também recebe `figs_dir` (onde os PNGs de diagnóstico são gravados,
padrão `BASE_DIR / "FIGs"`) e as flags `run_report`/`run_diagnostics` para pular a etapa 3 ou 2,
respectivamente (equivalentes a `--no-report`/`--no-diagnostics` na CLI).

### Onde ficam os resultados

Depois de rodar, `OUTPUT/` (ou o `output_dir` configurado) contém três arquivos com timestamp no
nome (`{sigla}{subsetor}_{AAAA-MM-DD_HHhMMm}`):

| Arquivo | Conteúdo |
|---|---|
| `ANALISE_DESCRITIVA_*.xlsx` | Planilhas `Descritivo` (estatísticas descritivas por indicador), `Winsorization` (limites/contagem de outliers cortados) e `BoxCox` (lambda e assimetria/curtose por indicador). |
| `DADOS_TRATADOS_*.xlsx` | Planilhas `BNivel 7` (dados brutos), `Winsorization`, `BoxCox` e `Normalizado` — os dados município a município em cada etapa de tratamento, cada uma precedida pelas colunas de referência `GEOCOD`/`MUN`/`UF`. |
| `REL_*.pptx` | O relatório PowerPoint: um grupo de slides por indicador (tabela descritiva + boxplot/histograma + mapa coroplético em cada etapa habilitada) mais um slide com o diagrama setorial. |

`FIGs/` (ou o `figs_dir` configurado) recebe 5 PNGs de diagnóstico gerados a partir do conjunto
completo de indicadores: `Contagem_NA_ISimples.png` (NAs por indicador), `Correlacao_Total.png` e
`Correlacao_Parcial.png` (correlogramas de Spearman total/parcial), `VIF_ISimples.png` (fator de
inflação de variância) e `AlphaCronbach_ISimples.png` (impacto de cada indicador no alfa de
Cronbach). As duas últimas células do notebook exibem esses PNGs inline após a execução.

## Limitações conhecidas

Um indicador classificado como "Cluster" produz 3 visões descritivas em `resumo.resumo_basico`
(Conjunto Completo/Grupo 1/Grupo 2), mas apenas 2 linhas de winsorização em `datawinz.resumo`
(Grupo 1/Grupo 2). O laço de slides por indicador em `slides_resultT` assume que essas linhas
correspondem 1:1, portanto ele lança um erro claro para conjuntos de dados com qualquer metadado
classificado como "Cluster", em vez de gerar slides desalinhados. O layout de relatório por
indicador para indicadores classificados como Cluster ainda não está implementado; os conjuntos de
dados de exemplo não têm linhas classificadas como Cluster, então isso não os afeta.

## Testes

```
pytest tests/
```

`tests/test_integration_report.py` e `tests/test_integration_treatment.py` exercitam o pipeline
completo com os ativos reais em `DATASET/`/`TEMPLATE/`; eles são pulados automaticamente se esses
arquivos ou (para o teste de relatório) uma instalação do Graphviz no sistema não estiverem
presentes.
