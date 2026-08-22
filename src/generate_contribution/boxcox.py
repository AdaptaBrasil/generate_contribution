"""Skew/kurtosis-gated Box-Cox transform.

A column is only transformed when it's both notably skewed (>= 2) and
notably peaked (raw kurtosis >= 3.5); otherwise the winsorized data passes
through unchanged. `method_boxcox` accepts `"forecast"` (default, MLE lambda
via `scipy.stats.boxcox`) or `"yeojohnson"` (`scipy.stats.yeojohnson`, handles
zero/negative values).

Only `Classe == "Numérico"` columns are transformable; Descricao/Score columns
are passed through unchanged (matching `winsorise.py`'s treatment of them).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


def skew(x: pd.Series) -> float:
    """Sample skewness (third standardized moment coefficient)."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if len(x) == 0:
        return np.nan
    m = x.mean()
    m2 = np.mean((x - m) ** 2)
    m3 = np.mean((x - m) ** 3)
    if m2 == 0:
        return np.nan
    return float(m3 / m2**1.5)


def kurt(x: pd.Series) -> float:
    """Raw (non-excess) sample kurtosis; normal ~= 3, used against the 3.5 gating threshold below."""
    x = pd.to_numeric(x, errors="coerce").dropna()
    if len(x) == 0:
        return np.nan
    m = x.mean()
    m2 = np.mean((x - m) ** 2)
    m4 = np.mean((x - m) ** 4)
    if m2 == 0:
        return np.nan
    return float(m4 / m2**2)


def sfunc_bxcx(y: pd.Series, metodo: str) -> pd.Series:
    """Applies the Box-Cox/Yeo-Johnson transform to the non-NA values of one column."""
    mask = y.notna()
    y_non_na = pd.to_numeric(y[mask], errors="coerce").astype(float).copy()
    y_non_na[y_non_na == 0] = y_non_na[y_non_na == 0] + 0.001

    if metodo == "yeojohnson":
        transformed, _lmbda = sp_stats.yeojohnson(y_non_na.to_numpy())
    else:
        transformed, _lmbda = sp_stats.boxcox(y_non_na.to_numpy())

    result = pd.Series(np.nan, index=y.index, dtype=float)
    result[mask] = transformed
    return result


@dataclass(slots=True)
class BoxCoxResult:
    meta: pd.DataFrame
    data: pd.DataFrame


def _prec_boxcox(
    data_win: pd.Series,
    dados: pd.Series,
    classe: str,
    nome: str,
    metodo: str,
) -> tuple[dict, pd.Series]:
    if classe != "Numérico":
        meta = dict(
            Nome=nome,
            Classe=classe,
            BoxCox=0,
            Distorcao=np.nan,
            Curtose=np.nan,
            Metodo=metodo,
        )
        return meta, data_win

    distorcao = skew(data_win)
    curtose = kurt(data_win)
    apply_boxcox = 0 if (pd.isna(distorcao) or pd.isna(curtose)) else int(distorcao >= 2 and curtose >= 3.5)

    meta = dict(
        Nome=nome,
        Classe="Numérico",
        BoxCox=apply_boxcox,
        Distorcao=distorcao,
        Curtose=curtose,
        Metodo=metodo,
    )

    data_bx = sfunc_bxcx(dados, metodo) if apply_boxcox == 1 else data_win
    return meta, data_bx


def ADPBoxCox(
    dadoswin: pd.DataFrame,
    dados: pd.DataFrame,
    classe: Sequence[str],
    cluster: pd.Series | None,
    nome: Sequence[str],
    metodo: str,
) -> BoxCoxResult:
    """Applies the skew/kurtosis-gated Box-Cox transform to every Numérico column."""
    metas = []
    data_cols = {}
    for i in range(dados.shape[1]):
        meta, data_bx = _prec_boxcox(dadoswin.iloc[:, i], dados.iloc[:, i], classe[i], nome[i], metodo)
        metas.append(meta)
        data_cols[nome[i]] = data_bx

    meta_df = pd.DataFrame(metas)
    data_df = pd.DataFrame(data_cols)
    return BoxCoxResult(meta=meta_df, data=data_df)
