from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from generate_contribution.boxcox import ADPBoxCox, kurt, skew, sfunc_bxcx


def test_skew_zero_for_symmetric_data():
    x = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    assert skew(x) == pytest.approx(0.0, abs=1e-9)


def test_kurt_raw_near_three_for_normal_like_sample():
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(size=5000))
    assert kurt(x) == pytest.approx(3.0, abs=0.3)


def test_sfunc_bxcx_preserves_na_positions():
    y = pd.Series([1.0, 2.0, np.nan, 4.0, 5.0, 0.0, 3.0])
    out = sfunc_bxcx(y, "forecast")
    assert out.isna().equals(y.isna())


def test_adpboxcox_passes_through_non_numerico_class():
    dados = pd.DataFrame({"X": [1.0, 2.0, 3.0]})
    result = ADPBoxCox(dados, dados, ["Score"], None, ["X"], "forecast")
    assert result.meta.loc[0, "Classe"] == "Score"
    assert result.meta.loc[0, "BoxCox"] == 0
    pd.testing.assert_series_equal(result.data["X"], dados["X"], check_names=False)


def test_adpboxcox_skips_transform_when_not_skewed():
    dados = pd.DataFrame({"X": [1.0, 2.0, 3.0, 4.0, 5.0]})
    result = ADPBoxCox(dados, dados, ["Numérico"], None, ["X"], "forecast")
    assert result.meta.loc[0, "BoxCox"] == 0
    pd.testing.assert_series_equal(result.data["X"], dados["X"], check_names=False)
