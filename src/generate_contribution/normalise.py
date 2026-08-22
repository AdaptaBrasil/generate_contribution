"""Min-max normalization.

Port of `SCRIPTS/FUNCTION/F04_ADPNormalise.r` (`sfunc_norm` / `ADPNormalise`).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def sfunc_norm(y: pd.Series) -> pd.Series:
    """Port of `sfunc_norm(Y)`: (x - min) / (max - min), NA-aware."""
    x = pd.to_numeric(y, errors="coerce").astype(float)
    if x.isna().all():
        # matches R's (NA-NA)/(NA-NA) -> NA, without numpy's all-NaN-slice warning
        return x
    xmax = np.nanmax(x)
    xmin = np.nanmin(x)
    return (x - xmin) / (xmax - xmin)


@dataclass(slots=True)
class NormaliseResult:
    idata: pd.DataFrame


def ADPNormalise(idata: pd.DataFrame) -> NormaliseResult:
    """Port of `ADPNormalise(iData)`."""
    data_norm = idata.apply(sfunc_norm, axis=0)
    return NormaliseResult(idata=data_norm)
