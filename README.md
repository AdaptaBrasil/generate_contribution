# generate_contribution

[![GitHub](https://img.shields.io/badge/GitHub-generate__contribution-blue?logo=github)](https://github.com/AdaptaBrasil/generate_contribution)
[![CI](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml/badge.svg)](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml)
[![Python 3.11 | 3.12 | 3.13 | 3.14](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python&logoColor=white)](https://github.com/AdaptaBrasil/generate_contribution/blob/master/.github/workflows/ci.yml)

AdaptaBrasil's indicator treatment and reporting pipeline: winsorization, Box-Cox, normalization,
correlation/VIF/Cronbach's alpha diagnostics, and a PowerPoint report (with per-indicator maps and
a sector diagram).

## Getting started

### What it does

`generate_contribution` turns a raw AdaptaBrasil indicator spreadsheet into a validated,
report-ready dataset, in three stages:

1. **Treatment** — winsorizes outliers, applies a skew/kurtosis-gated Box-Cox transform, and
   min-max normalizes every indicator, writing two Excel workbooks (a descriptive-statistics
   summary and the treated data at each stage).
2. **Diagnostics** — Spearman/partial correlation, VIF, and Cronbach's alpha (with automatic
   reverse-keying), plus the four PNG diagnostic charts (NA counts, two correlograms, VIF, alpha
   impact).
3. **Report** — a PowerPoint deck with one slide group per indicator (descriptive table +
   boxplot/histogram + choropleth map, at each of the raw/winsorized/Box-Cox/normalized stages),
   plus a sector diagram slide.

Stage 1 always runs; stages 2 and 3 are optional (`--no-diagnostics`/`--no-report` on the
`pipeline` command, see below).

### 1. Get the files

```
git clone https://github.com/AdaptaBrasil/generate_contribution.git
cd generate_contribution
```

The sample dataset, shapefiles, and PPTX template needed to run the pipeline are already included
under `DATASET/`/`TEMPLATE/` (see "Data assets" below) — nothing else to download to try it out.

### 2. Create a virtual environment

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

### 3. Install the package and its dependencies

```
pip install -e ".[dev]"
```

This installs the library, the `generate-contribution` CLI, and everything under
`[project.dependencies]` in `pyproject.toml` (pandas, numpy, scipy, geopandas, python-pptx, etc.);
`[dev]` additionally pulls in `pytest` to run the test suite. Drop `[dev]` if you only need to run
the pipeline.

The diagram step (`generate_contribution.diagrams`) additionally requires a system **Graphviz**
install (the `dot` executable on PATH) — e.g. `winget install Graphviz.Graphviz` on Windows,
`apt install graphviz` / `dnf install graphviz` on Linux.

### 4. Parameters

The CLI has two subcommands. `generate-contribution tratamento` runs stage 1 only:

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--input` | yes | — | Path to the input `.xlsx` workbook. |
| `--imeta-sheet` | no | `Metadados` | Sheet name holding indicator metadata (`Nivel`/`Code`/`Nome`/`Pai`/`Classe` columns). |
| `--idata-sheet` | yes | — | Sheet name holding the raw data (`GEOCOD`/`MUN`/`UF`/`CLUSTER` + one column per indicator). |
| `--method-boxcox` | no | `forecast` | Box-Cox engine: `forecast` (MLE lambda) or `yeojohnson`. |
| `--sigla` | no | `SE` | Short code used in output filenames (e.g. `SA`). |
| `--subsetor` | no | — | Appended to `--sigla` in filenames and report titles (e.g. `ACESSO`). |
| `--output-dir` | no | `OUTPUT` | Directory the two output `.xlsx` files are written to. |

`generate-contribution pipeline` runs all three stages and accepts every flag above, plus:

| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--template` | yes | — | PPTX template path (e.g. `TEMPLATE/ADAPTA_RESUMO.pptx`). |
| `--setor-estrategico` | yes | — | Sector name shown on the report's title slide. |
| `--shp-mun` | yes | — | Municipality boundaries shapefile (`.shp`). |
| `--shp-uf` | yes | — | State boundaries shapefile (`.shp`). |
| `--ind` | no | all | Limit the report to the first N indicators — handy for a quick smoke test before running the full deck. |
| `--figs-dir` | no | `FIGs` | Directory the diagnostic PNGs are written to. |
| `--no-report` | no | off | Skip PPTX generation (treatment + diagnostics only). |
| `--no-diagnostics` | no | off | Skip correlation/VIF/Cronbach diagnostics and figures. |

See the "CLI" section below for full example invocations.

## Module reference

| Python module | Responsibility |
|---|---|
| `cli.py`, `pipeline.py` | CLI entry points and top-level pipeline orchestration |
| `resumo.py` | Descriptive statistics (boxplot stats, per-indicator/per-cluster summaries) |
| `winsorise.py` | Winsorization (outlier clipping) |
| `boxcox.py` | Skew/kurtosis-gated Box-Cox transform |
| `normalise.py` | Min-max normalization |
| `treatment.py`, `io_excel.py` | End-to-end treatment orchestration + Excel I/O |
| `correlation.py` | Correlation/VIF/Cronbach's alpha diagnostics |
| `figures.py` | Diagnostic and per-indicator PNG charts |
| `maps.py` | Choropleth maps |
| `diagrams.py` | Sector diagram |
| `pptx_report.py` | PowerPoint report assembly |

## Data assets

`DATASET/` and `TEMPLATE/` hold real, ready-to-run assets, so this project runs standalone:

- `DATASET/Base_inicial_SA_Acesso.xlsx` — sample input workbook (`Metadados` + `Dados_RA_Acesso` sheets).
- `DATASET/Base_inicial_RH_INDBRT.xlsx` — a second sample workbook (`Metadados` + `Dados_RH_INDBRT`
  sheets); its metadata's parent-indicator column was renamed from `Parente` to `Pai` on import to
  match the schema `diagrams.py`/`resumo.py` expect. Includes a `Cluster`-classified indicator, so
  running the PPTX report against it currently hits the Cluster limitation noted below — treatment
  and diagnostics run fine.
- `DATASET/SHP/BR_Municipios_2022_gr.*`, `DATASET/SHP/BR_UF_2022_gr.*` — municipality/state boundary shapefiles used by `maps.py`.
- `TEMPLATE/ADAPTA_RESUMO.pptx` — PPTX template used by `pptx_report.py`.
- `DESCRITORES/DESCRITORES.xlsx`, `DESCRITORES/DIGRAMA_RH.pdf` — human reference docs, not read by any code.

## CLI

```
# Treatment only (winsorize/Box-Cox/normalize + the two output workbooks)
generate-contribution tratamento \
  --input DATASET/Base_inicial_SA_Acesso.xlsx --idata-sheet Dados_RA_Acesso \
  --sigla SA --subsetor ACESSO --output-dir OUTPUT

# Full pipeline: treatment -> PPTX report -> correlation/VIF/Cronbach diagnostics + figures
generate-contribution pipeline \
  --input DATASET/Base_inicial_SA_Acesso.xlsx --idata-sheet Dados_RA_Acesso \
  --sigla SA --subsetor ACESSO \
  --template TEMPLATE/ADAPTA_RESUMO.pptx --setor-estrategico "Segurança Alimentar" \
  --shp-mun DATASET/SHP/BR_Municipios_2022_gr.shp --shp-uf DATASET/SHP/BR_UF_2022_gr.shp \
  --output-dir OUTPUT --figs-dir FIGs
```

## Known data-quality caveat

`winsorise.py` joins data columns to `Metadados.Code` by **exact name match**. The sample
`Base_inicial_SA_Acesso.xlsx` has several data-sheet column headers with stray leading/trailing
spaces (e.g. `"MMPD "`, `" ODRSAI"`) that don't match the clean `Code` values in `Metadados` —
those columns come out all-NA after winsorization, and get excluded downstream. Fix by trimming
the data sheet's column headers at the source if you want those indicators included.

## Known limitations

A "Cluster"-classified indicator produces 3 descriptive views in `resumo.resumo_basico` (Conjunto
Completo/Grupo 1/Grupo 2) but only 2 winsorization rows in `datawinz.resumo` (Grupo 1/Grupo 2).
`slides_resultT`'s per-indicator slide loop assumes those line up 1:1, so it raises a clear error
for datasets with any "Cluster"-classified metadata rather than emitting misaligned slides.
Per-indicator report layout for Cluster-classified indicators isn't implemented yet; the sample
datasets have no Cluster-classified rows, so this doesn't affect them.

## Tests

```
pytest tests/
```

`tests/test_integration_report.py` and `tests/test_integration_treatment.py` exercise the full
pipeline against the real assets in `DATASET/`/`TEMPLATE/`; they skip automatically if those files
or (for the report test) a system Graphviz install aren't present.
