"""Winsorization.

Port of `SCRIPTS/FUNCTION/F02_ADPwinsorise.r` (`wins_par` / `winsorise1` / `ADPwinsorise`).

The source R script has three behavioral bugs that this port fixes rather
than reproduces (see project history for the earlier, literal port):

1. `winsorise1` computed "Grupo 1"/"Grupo 2" winsorization limits over the
   Numérico columns (reusing that column-index vector by mistake) instead of
   the columns actually classified as "Cluster" in `iMeta`. Fixed: Grupo 1/2
   limits are computed from the "Cluster"-classified columns.
2. `ADPwinsorise` applied the "Numérico"/"Grupo 1"/"Grupo 2" results as three
   sequential whole-column overwrites, so only the last one applied survived
   for rows outside its own cluster subset. Fixed: for a "Cluster"-classified
   column, Grupo 1 and Grupo 2 clipping are merged into one column (each
   applied only to its own CLUSTER subset, starting from the same raw data),
   instead of one clobbering the other.
3. Columns classified as "Descricao" or "Score" were never populated (a dead
   branch in the R script meant to copy them through was unreachable). Fixed:
   such columns are copied through unchanged, matching the source project's
   own README ("Score_ADP = 1 ... Não Aplicar Winsorization").
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def wins_par(y: pd.Series, a: str, b: str) -> dict:
    """Port of `wins_par(Y, a, b)`: winsorization limits for one column."""
    x = pd.to_numeric(y, errors="coerce").to_numpy(dtype=float)
    xn = x[~np.isnan(x)]

    ol_inf = np.min(xn) if len(xn) else np.nan
    ol_sup = np.max(xn) if len(xn) else np.nan

    q1 = np.nanquantile(x, 0.25)
    q3 = np.nanquantile(x, 0.75)
    iqr = q3 - q1
    tl_inf = q1 - 1.5 * iqr
    tl_sup = q3 + 1.5 * iqr

    l_inf = max(ol_inf, tl_inf)
    l_sup = ol_sup if tl_sup == 0 else min(ol_sup, tl_sup)

    if l_inf != ol_inf and l_sup != ol_sup:
        awin = "A"
    elif l_inf == ol_inf and l_sup != ol_sup:
        awin = "S"
    elif l_inf != tl_inf and l_sup == ol_sup:
        awin = "I"
    else:
        awin = "N"

    n_na = int(np.isnan(x).sum())
    t_outlier = int(np.sum((xn > l_sup) | (xn < l_inf)))

    return dict(
        iName=b,
        Classe=a,
        Aplicacao=awin,
        LINF=round(float(l_inf), 2),
        LSUP=round(float(l_sup), 2),
        T_outlier=t_outlier,
        T_NA=n_na,
    )


def winsorise1(idata: pd.DataFrame, imeta: pd.DataFrame, iref: pd.Series) -> pd.DataFrame:
    """Port of `winsorise1(iData, iMeta, iRef)`.

    Numérico columns get one "Numérico" row (limits from the full column).
    Cluster columns get "Grupo 1"/"Grupo 2" rows (limits from the CLUSTER==1 /
    CLUSTER==2 row subsets of that same column).
    """
    numerico_codes = set(imeta.loc[imeta["Classe"] == "Numérico", "Code"])
    cluster_codes = set(imeta.loc[imeta["Classe"] == "Cluster", "Code"])
    numeric_cols = [c for c in idata.columns if c in numerico_codes]
    cluster_cols = [c for c in idata.columns if c in cluster_codes]

    rows = [wins_par(idata[c], "Numérico", c) for c in numeric_cols]

    if cluster_cols:
        iref = pd.Series(iref).reset_index(drop=True)
        idata_r = idata.reset_index(drop=True)
        grupo1_mask = iref == 1
        grupo2_mask = iref == 2
        rows += [wins_par(idata_r.loc[grupo1_mask, c], "Grupo 1", c) for c in cluster_cols]
        rows += [wins_par(idata_r.loc[grupo2_mask, c], "Grupo 2", c) for c in cluster_cols]

    resumo = pd.DataFrame(rows)

    code_order = {code: i for i, code in enumerate(imeta["Code"])}
    resumo["_order"] = resumo["iName"].map(code_order)
    resumo = resumo.sort_values("_order", kind="stable").drop(columns="_order").reset_index(drop=True)
    return resumo


@dataclass(slots=True)
class WinsoriseResult:
    resumo: pd.DataFrame
    idata: pd.DataFrame


def ADPwinsorise(idata: pd.DataFrame, imeta: pd.DataFrame, iref: pd.Series) -> WinsoriseResult:
    """Port of `ADPwinsorise(iData, iMeta, iRef)`."""
    resumo1 = winsorise1(idata, imeta, iref)
    iref = pd.Series(iref).reset_index(drop=True)
    idata_r = idata.reset_index(drop=True)

    passthrough_codes = set(imeta.loc[imeta["Classe"].isin(["Descricao", "Score"]), "Code"])

    dados_out = idata_r.copy()
    dados_out.iloc[:, :] = np.nan

    for col in dados_out.columns:
        if col in passthrough_codes:
            dados_out[col] = idata_r[col]
            continue

        col_rows = resumo1[resumo1["iName"] == col]
        if col_rows.empty:
            continue  # no matching iMeta entry for this column -> left as NaN

        whole = idata_r[col].copy()
        applied = False
        for _, row in col_rows.iterrows():
            classe = row["Classe"]
            linf, lsup = float(row["LINF"]), float(row["LSUP"])
            if classe == "Numérico":
                whole = idata_r[col].clip(lower=linf, upper=lsup)
                applied = True
            elif classe == "Grupo 1":
                mask = iref == 1
                whole[mask] = whole[mask].clip(lower=linf, upper=lsup)
                applied = True
            elif classe == "Grupo 2":
                mask = iref == 2
                whole[mask] = whole[mask].clip(lower=linf, upper=lsup)
                applied = True

        if applied:
            dados_out[col] = whole

    return WinsoriseResult(resumo=resumo1, idata=dados_out)
