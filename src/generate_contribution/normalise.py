"""Min-max normalization: rescales every column to [0, 1]."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def sfunc_norm(y: pd.Series) -> pd.Series:
    """(x - min) / (max - min), NA-aware."""
    x = pd.to_numeric(y, errors="coerce").astype(float)
    if x.isna().all():
        # an all-NaN column stays all-NaN, without numpy's all-NaN-slice warning
        return x
    xmax = np.nanmax(x)
    xmin = np.nanmin(x)
    return (x - xmin) / (xmax - xmin)


@dataclass(slots=True)
class NormaliseResult:
    idata: pd.DataFrame


def ADPNormalise(idata: pd.DataFrame) -> NormaliseResult:
    """Min-max normalizes every column of `idata`."""
    data_norm = idata.apply(sfunc_norm, axis=0)
    return NormaliseResult(idata=data_norm)
