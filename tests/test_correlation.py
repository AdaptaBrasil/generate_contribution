from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from generate_contribution.correlation import (
    ADPAlphaCron,
    ADPcorrel,
    ADPcorrel_parcial,
    ADPvif,
    correl_ind,
    get_max_cor,
)


@pytest.fixture
def correlated_df() -> pd.DataFrame:
    rng = np.random.default_rng(1)
    n = 200
    a = rng.normal(size=n)
    b = a + rng.normal(scale=0.05, size=n)  # near-duplicate of a
    c = rng.normal(size=n)  # independent
    return pd.DataFrame({"A": a, "B": b, "C": c})


def test_get_max_cor_excludes_self():
    mat = pd.DataFrame([[1.0, 0.9, 0.2], [0.9, 1.0, 0.1], [0.2, 0.1, 1.0]], index=["A", "B", "C"], columns=["A", "B", "C"])
    result = get_max_cor(mat)
    assert result.loc["A", "Par"] == "B"
    assert result.loc["A", "Max"] == pytest.approx(0.9)


def test_adpcorrel_detects_strong_pair(correlated_df):
    result = ADPcorrel(correlated_df)
    assert result.cor_summary.loc["A", "Cor_Par"] == "B"
    assert result.cor_summary.loc["A", "Cor_Max"] > 0.9


def test_adpvif_high_for_collinear_columns(correlated_df):
    vif_df = ADPvif(correlated_df).set_index("Indicador")
    assert vif_df.loc["A", "VIF"] > 5  # A and B are near-duplicates -> high VIF
    assert vif_df.loc["C", "VIF"] < 2  # C is independent -> low VIF


def test_adpcorrel_parcial_shape(correlated_df):
    result = ADPcorrel_parcial(correlated_df)
    assert result.pcorrel.shape == (3, 3)
    assert (result.pcorrel.to_numpy() >= 0).all()  # abs() applied


def test_adpalphacron_reverses_negatively_related_item():
    rng = np.random.default_rng(2)
    n = 300
    base = rng.normal(size=n)
    df = pd.DataFrame(
        {
            "P1": base + rng.normal(scale=0.1, size=n),
            "P2": base + rng.normal(scale=0.1, size=n),
            "P3": -base + rng.normal(scale=0.1, size=n),  # inversely related
        }
    )
    result = ADPAlphaCron(df)
    assert "-P3" in result.keys
    assert 0 <= result.alpha_total <= 1


def test_correl_ind_end_to_end(correlated_df):
    result = correl_ind(correlated_df, na_count_threshold=55)
    assert set(result.resumo["Indicador"]) == {"A", "B", "C"}
    assert result.resumo.set_index("Indicador").loc["A", "Sugestao_Remocao"] == "Remover (Correl alta)"


def test_correl_ind_excludes_high_na_columns():
    rng = np.random.default_rng(0)
    df = pd.DataFrame(
        {
            "GOOD1": rng.normal(size=100),
            "GOOD2": rng.normal(size=100),
            "BAD": [np.nan] * 60 + list(rng.normal(size=40)),
        }
    )
    result = correl_ind(df, na_count_threshold=55)
    assert "BAD" in result.indicadores_na
    assert "BAD" not in result.resumo["Indicador"].tolist()
