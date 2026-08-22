from __future__ import annotations

import numpy as np
import pandas as pd

from generate_contribution.correlation import ADPAlphaCron, ADPvif, correl_ind
from generate_contribution.figures import (
    FigContNA,
    FigCorrelPlot,
    FigVIF,
    criar_grafico,
    grafico_final,
    plotAlphaCronbach,
)


def test_all_figures_produce_nonempty_png(tmp_path):
    rng = np.random.default_rng(3)
    df = pd.DataFrame(
        {
            "A": rng.normal(size=150),
            "B": rng.normal(size=150),
            "C": rng.normal(size=150),
        }
    )
    result = correl_ind(df)

    na_png = tmp_path / "na.png"
    FigContNA(result.contagem_na, na_png)
    assert na_png.exists() and na_png.stat().st_size > 0

    corr_png = tmp_path / "corr.png"
    FigCorrelPlot(result.correl, tipo="Total", nfile=corr_png)
    assert corr_png.exists() and corr_png.stat().st_size > 0

    vif_png = tmp_path / "vif.png"
    FigVIF(result.vif, vif_png)
    assert vif_png.exists() and vif_png.stat().st_size > 0

    alpha_png = tmp_path / "alpha.png"
    plotAlphaCronbach(result.alpha_cronbach, alpha_png)
    assert alpha_png.exists() and alpha_png.stat().st_size > 0


def test_criar_grafico_and_grafico_final(tmp_path):
    rng = np.random.default_rng(4)
    raw = pd.Series(rng.normal(loc=10, scale=2, size=100))

    combo_png = tmp_path / "combo.png"
    criar_grafico(raw, combo_png, nvalores="IND1")
    assert combo_png.exists() and combo_png.stat().st_size > 0

    normalized = (raw - raw.min()) / (raw.max() - raw.min())
    df1 = pd.DataFrame({"Normalizado": normalized, "N_Normalizado": raw})
    df = pd.DataFrame({"IND1": normalized})
    final_png = tmp_path / "final.png"
    grafico_final(df1, df, final_png, nvalores="IND1")
    assert final_png.exists() and final_png.stat().st_size > 0
