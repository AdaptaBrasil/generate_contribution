# generate_contribution

[![GitHub](https://img.shields.io/badge/GitHub-generate__contribution-blue?logo=github)](https://github.com/AdaptaBrasil/generate_contribution)
[![CI](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml/badge.svg)](https://github.com/AdaptaBrasil/generate_contribution/actions/workflows/ci.yml)

Python port of [`ScriptRCalculoContribuicao`](../ScriptRCalculoContribuicao): the AdaptaBrasil
indicator treatment pipeline (winsorization, Box-Cox, normalization), correlation/VIF/Cronbach's
alpha diagnostics, and the PowerPoint report (with per-indicator maps and a sector diagram).

Numeric parity with the R script is **functionally equivalent, not bit-exact** (see "Library
mapping" below) — statistical concepts and thresholds are preserved; the underlying numerical
libraries differ from R's COINr/forecast/corpcor/psych/car stack.

## Install

```
pip install -e ".[dev]"
```

The diagram step (`generate_contribution.diagrams`) additionally requires a system **Graphviz**
install (the `dot` executable on PATH) — e.g. `winget install Graphviz.Graphviz` on Windows,
`apt install graphviz` / `dnf install graphviz` on Linux.

## Module map (R file -> Python module)

| R file | Python module |
|---|---|
| `AA01-INICIO_DESCRITIVO_INDICADORES.R` | `cli.py`, `pipeline.py` |
| `FUNCTION/F01_ADPResumo.r` | `resumo.py` |
| `FUNCTION/F02_ADPwinsorise.r` | `winsorise.py` |
| `FUNCTION/F03_ADPBoxCox.r` | `boxcox.py` |
| `FUNCTION/F04_ADPNormalise.r` | `normalise.py` |
| `FUNCTION/F07_ADP_GeraExcell.r` | `treatment.py`, `io_excel.py` |
| `FUNCTION/F08_ADPCORREL.r` | `correlation.py` (stats) + `figures.py` (plots) |
| `FUNCTION/F05_ADPGraficos.r` | `figures.py` (charts), `maps.py` (choropleths), `diagrams.py` (sector diagram) |
| `FUNCTION/F06_ADPCriar_pptx_E01.R` | `pptx_report.py` |

## Data assets

`DATASET/` and `TEMPLATE/` hold real, ready-to-run assets copied from the source R project
(`ScriptRCalculoContribuicao`), so this project runs standalone:

- `DATASET/Base_inicial_SA_Acesso.xlsx` — sample input workbook (`Metadados` + `Dados_RA_Acesso` sheets).
- `DATASET/SHP/BR_Municipios_2022_gr.*`, `DATASET/SHP/BR_UF_2022_gr.*` — municipality/state boundary shapefiles used by `maps.py`.
- `TEMPLATE/ADAPTA_RESUMO.pptx` — PPTX template used by `pptx_report.py`.

Not copied over (present in the source R project but unused by this pipeline, or R-specific):
`IData_RH_INDBRT.csv`/`IMeta_RH_INDBRT.csv` (an older, unused COINr-direct format),
`Exemplo_BoxCox.csv` (a standalone tutorial script's data), `FUN_VALORES_DES_INUND_*.xlsx` (a
manually-built lookup table for an unrelated sector), and the R project's own `OUTPUT`/`FIGs`
(regenerable) and `.RData`/`.Rhistory` (R session state). `Base_inicial_RH_INDBRT.xlsx` (a second
real dataset, same schema except its metadata sheet uses `Parente` instead of `Pai`) and
`DESCRITORES/` (human reference docs) were left out too — ask if you want either brought over.

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

## Library mapping (R -> Python)

| R | Python |
|---|---|
| `boxplot.stats` (Tukey hinges via `fivenum`) | `resumo.fivenum` / `resumo.boxplot_stats` (hand-implemented, matches R's algorithm) |
| `forecast::BoxCox.lambda`/`BoxCox` | `scipy.stats.boxcox` (MLE lambda, not Guerrero) |
| `bestNormalize::yeojohnson` | `scipy.stats.yeojohnson` |
| `COINr::skew`/`COINr::kurt` | hand-implemented moment-based skew / raw kurtosis |
| `Hmisc::rcorr(type="spearman")` | `scipy.stats.spearmanr` |
| `corpcor::pcor.shrink` | Ledoit-Wolf shrinkage covariance (`sklearn.covariance.LedoitWolf`) inverted to partial correlation |
| `car::vif` | `statsmodels` `variance_inflation_factor` |
| `psych::alpha(check.keys=TRUE)` | hand-implemented Cronbach's alpha with alpha-if-dropped + sign-based auto reverse-keying |
| `sf`/`ggplot2::geom_sf`, `corrplot` | `geopandas` + `matplotlib` |
| `DiagrammeR`/`rsvg` | `graphviz` (Python wrapper around system Graphviz) |
| `officer`/`flextable` | `python-pptx` |

## Known data-quality caveat (not a port bug)

`winsorise.py` joins data columns to `Metadados.Code` by **exact name match**, mirroring the R
script's `%in%` join. The sample `Base_inicial_SA_Acesso.xlsx` has several data-sheet column
headers with stray leading/trailing spaces (e.g. `"MMPD "`, `" ODRSAI"`) that don't match the
clean `Code` values in `Metadados` — this affects both the R and Python pipelines identically
(those columns come out all-NA after winsorization, and get excluded downstream). Fix by trimming
the data sheet's column headers at the source if you want those indicators included.

## Behavioral bugs in the R script that this port fixes (not reproduces)

Earlier versions of this port deliberately reproduced these for output parity; they are now
fixed, since they're clearly unintended (each is documented with an inline comment at the point
it occurs):

- `resumo.py`: per-cluster Min/Q1/Median/Q3/Max in `criar_resumo`'s Cluster branch now come from
  each cluster's own subset, not the full column (the R script computed them from the full column
  for every group).
- `winsorise.py`:
  - Grupo 1/Grupo 2 winsorization limits are now computed from columns actually classified as
    "Cluster" in `iMeta` (the R script re-used the Numérico column list by mistake, so it
    winsorized the wrong columns per cluster).
  - For a Cluster-classified column, Grupo 1 and Grupo 2 clipping are now merged into one column
    (each applied only to its own CLUSTER subset). The R script applied Numérico/Grupo 1/Grupo 2
    as three sequential whole-column overwrites, so only the last one applied (Grupo 2, when
    present) survived — Grupo 1's clipping was silently discarded.
  - Columns classified as "Descricao" or "Score" are now passed through unchanged, matching the
    source project's own README ("Score_ADP = 1 ... Não Aplicar Winsorization"). The R script had
    a dead code branch that was meant to do this but could never execute, so those columns came
    back entirely empty.
- `pptx_report.py`: the Shapiro-Wilk test is run on the actual data (the R script's version
  references an undefined variable and always falls back to a placeholder string).

One structural gap remains **unresolved by design**, not silently patched over: a
"Cluster"-classified indicator now legitimately produces 3 descriptive views in
`resumo.resumo_basico` (Conjunto Completo/Grupo 1/Grupo 2) but only 2 winsorization rows in
`datawinz.resumo` (Grupo 1/Grupo 2). `slides_resultT`'s per-indicator slide loop assumes those line
up 1:1, so it raises a clear error for datasets with any "Cluster"-classified metadata rather than
emitting misaligned slides. The source R project's own README flags Cluster-indicator handling as
still to be designed ("fazer avaliação depois"); the sample datasets have no Cluster-classified
rows, so this doesn't affect them.

## Tests

```
pytest tests/
```

`tests/test_integration_report.py` and `tests/test_integration_treatment.py` exercise the full
pipeline against the real assets in `DATASET/`/`TEMPLATE/`; they skip automatically if those files
or (for the report test) a system Graphviz install aren't present.
