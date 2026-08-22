from __future__ import annotations

import numpy as np
import pandas as pd

from generate_contribution.normalise import ADPNormalise, sfunc_norm


def test_sfunc_norm_range_zero_to_one():
    y = pd.Series([0.0, 5.0, 10.0, np.nan])
    out = sfunc_norm(y)
    assert out.min() == 0.0
    assert out.max() == 1.0
    assert pd.isna(out.iloc[3])


def test_adpnormalise_all_columns_bounded():
    df = pd.DataFrame({"A": [1.0, 2.0, 3.0], "B": [10.0, 20.0, 15.0]})
    result = ADPNormalise(df)
    assert result.idata["A"].tolist() == [0.0, 0.5, 1.0]
    assert result.idata["B"].min() == 0.0
    assert result.idata["B"].max() == 1.0
