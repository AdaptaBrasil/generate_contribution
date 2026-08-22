"""Correlation / VIF / Cronbach's alpha diagnostics.

Port of `SCRIPTS/FUNCTION/F08_ADPCORREL.r` (statistics functions only; figure
functions from that same file live in `figures.py`).

Library mapping (functionally, not bit-for-bit, equivalent to the R script):
- `Hmisc::rcorr(type="spearman")`  -> `scipy.stats.spearmanr`
- `corpcor::pcor.shrink`           -> Ledoit-Wolf shrinkage covariance
                                       (`sklearn.covariance.LedoitWolf`) inverted
                                       into a partial-correlation matrix
- `car::vif`                       -> `statsmodels` variance_inflation_factor
- `psych::alpha(check.keys=TRUE)`  -> custom Cronbach's alpha with per-item
                                       alpha-if-dropped and automatic reverse
                                       keying (sign of item-vs-rest correlation)
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as sp_stats
from sklearn.covariance import LedoitWolf
from statsmodels.stats.outliers_influence import variance_inflation_factor


def total_na(x: pd.Series) -> int:
    """Port of `total.na(x)`."""
    return int(x.isna().sum())


def get_max_cor(cor_matrix: pd.DataFrame) -> pd.DataFrame:
    """Port of `get_max_cor`: for each variable, the strongest (already-abs) pairing."""
    max_vals = []
    max_vars = []
    for col in cor_matrix.columns:
        others = cor_matrix[col].drop(index=col)
        max_vals.append(others.max())
        max_vars.append(others.idxmax())
    return pd.DataFrame({"Max": max_vals, "Par": max_vars}, index=cor_matrix.columns)


@dataclass(slots=True)
class ADPcorrelResult:
    cor_mat: pd.DataFrame
    p_mat: pd.DataFrame
    cor_summary: pd.DataFrame  # columns: Cor_Max, Cor_Par


def ADPcorrel(x: pd.DataFrame) -> ADPcorrelResult:
    """Port of `ADPcorrel(X)`: Spearman correlation matrix + p-values."""
    cols = list(x.columns)
    if len(cols) < 2:
        raise ValueError("ADPcorrel requires at least 2 columns to compute a correlation matrix.")
    if len(cols) == 2:
        rho, pval = sp_stats.spearmanr(x.iloc[:, 0], x.iloc[:, 1])
        rho_mat = np.array([[1.0, rho], [rho, 1.0]])
        p_arr = np.array([[0.0, pval], [pval, 0.0]])
    else:
        rho_mat, p_arr = sp_stats.spearmanr(x.to_numpy())

    cor_mat = pd.DataFrame(np.abs(rho_mat), index=cols, columns=cols)
    p_mat = pd.DataFrame(p_arr, index=cols, columns=cols)

    summary = get_max_cor(cor_mat)
    summary.columns = ["Cor_Max", "Cor_Par"]
    return ADPcorrelResult(cor_mat=cor_mat, p_mat=p_mat, cor_summary=summary)


@dataclass(slots=True)
class ADPcorrelParcialResult:
    pcorrel: pd.DataFrame
    pcor_summary: pd.DataFrame  # columns: Pcor_Max, Pcor_Par


def ADPcorrel_parcial(x: pd.DataFrame) -> ADPcorrelParcialResult:
    """Port of `ADPcorrel_parcial(X)`: shrinkage partial correlation."""
    cols = list(x.columns)
    cov = LedoitWolf().fit(x.to_numpy()).covariance_
    precision = np.linalg.inv(cov)
    d = np.sqrt(np.diag(precision))
    pcor = -precision / np.outer(d, d)
    np.fill_diagonal(pcor, 1.0)
    pcor = np.abs(pcor)

    pcorrel = pd.DataFrame(pcor, index=cols, columns=cols)
    summary = get_max_cor(pcorrel)
    summary.columns = ["Pcor_Max", "Pcor_Par"]
    return ADPcorrelParcialResult(pcorrel=pcorrel, pcor_summary=summary)


def ADPvif(x: pd.DataFrame) -> pd.DataFrame:
    """Port of `ADPvif(X)`: variance inflation factors via an intercept-augmented design matrix."""
    design = np.column_stack([np.ones(len(x)), x.to_numpy()])
    vifs = [variance_inflation_factor(design, i) for i in range(1, design.shape[1])]
    return pd.DataFrame({"Indicador": list(x.columns), "VIF": np.round(vifs, 3)})


@dataclass(slots=True)
class ADPAlphaCronResult:
    alpha_df: pd.DataFrame  # columns: Indicador, Alpha_if_Dropped
    alpha_drop: pd.Series  # indexed by Indicador
    alpha_total: float
    keys: list[str]  # item names, reversed items prefixed with "-"


def _cronbach_alpha(cov: np.ndarray) -> float:
    k = cov.shape[0]
    if k < 2:
        return float("nan")
    item_var_sum = np.trace(cov)
    total_var = cov.sum()
    if total_var == 0:
        return float("nan")
    return float(k / (k - 1) * (1 - item_var_sum / total_var))


def ADPAlphaCron(x: pd.DataFrame) -> ADPAlphaCronResult:
    """Port of `ADPAlphaCron(X)`: Cronbach's alpha with auto reverse-keying and alpha-if-dropped.

    Reverse-keying: an item whose correlation with the sum of the *other*
    items is negative is treated as reverse-scored (sign-flipped) before the
    alpha/covariance calculations, matching `psych::alpha(check.keys=TRUE)`'s
    intent. Cronbach's alpha depends only on item variances/covariances, both
    of which are invariant between sign-flip and psych's item-reflection, so
    this is a functionally equivalent substitute.
    """
    cols = list(x.columns)
    values = x.to_numpy(dtype=float)
    n_items = values.shape[1]

    totals_excl = values.sum(axis=1, keepdims=True) - values
    keys = np.ones(n_items)
    for j in range(n_items):
        r = np.corrcoef(values[:, j], totals_excl[:, j])[0, 1]
        if not np.isnan(r) and r < 0:
            keys[j] = -1.0

    keyed = values * keys
    cov = np.cov(keyed, rowvar=False)
    if cov.ndim == 0:
        cov = cov.reshape(1, 1)

    alpha_total = _cronbach_alpha(cov)

    alpha_dropped = []
    for j in range(n_items):
        idx = [i for i in range(n_items) if i != j]
        sub_cov = cov[np.ix_(idx, idx)]
        alpha_dropped.append(_cronbach_alpha(sub_cov))

    alpha_df = pd.DataFrame({"Indicador": cols, "Alpha_if_Dropped": np.round(alpha_dropped, 3)})
    alpha_drop = pd.Series(np.round(alpha_dropped, 3), index=cols)
    key_names = [f"-{c}" if k < 0 else c for c, k in zip(cols, keys)]

    return ADPAlphaCronResult(alpha_df=alpha_df, alpha_drop=alpha_drop, alpha_total=alpha_total, keys=key_names)


@dataclass(slots=True)
class CorrelIndResult:
    contagem_na: pd.Series
    indicadores_na: list[str]
    correl: pd.DataFrame
    p_value_cor: pd.DataFrame
    pcorrel: pd.DataFrame
    vif: pd.DataFrame
    alpha_cronbach: ADPAlphaCronResult
    indicadores_invertidos: list[str]
    resumo: pd.DataFrame


def correl_ind(x: pd.DataFrame, na_count_threshold: int = 55) -> CorrelIndResult:
    """Port of `correl_ind(x)`.

    `na_count_threshold` mirrors the source script's literal `cont.NA <= 55`
    cutoff (an absolute NA count, not a percentage).
    """
    cont_na = x.apply(total_na)
    col_select = cont_na[cont_na <= na_count_threshold].index.tolist()
    indicadores_removidas_nas = [c for c in x.columns if c not in col_select]
    dados = x[col_select].dropna()

    cor_result = ADPcorrel(dados)
    pcor_result = ADPcorrel_parcial(dados)
    vif_df = ADPvif(dados)
    alpha_result = ADPAlphaCron(dados)

    resumo_df = pd.DataFrame(
        {
            "Indicador": list(dados.columns),
            "Cor_Max": cor_result.cor_summary["Cor_Max"].round(3).to_numpy(),
            "Cor_Par_Indicador": cor_result.cor_summary["Cor_Par"].to_numpy(),
            "Pcor_Shrink_Max": pcor_result.pcor_summary["Pcor_Max"].round(3).to_numpy(),
            "Pcor_Par_Indicador": pcor_result.pcor_summary["Pcor_Par"].to_numpy(),
            "VIF": vif_df["VIF"].to_numpy(),
            "Alpha_Drop": alpha_result.alpha_drop.round(3).to_numpy(),
        }
    )

    def _sugestao(row: pd.Series) -> str:
        if row["Cor_Max"] >= 0.6:
            return "Remover (Correl alta)"
        if row["VIF"] >= 5:
            return "Remover (VIF alto)"
        if row["Pcor_Shrink_Max"] >= 0.6:
            return "Remover (Pcor alta)"
        if row["Alpha_Drop"] > alpha_result.alpha_total:
            return "Remover (melhora alpha)"
        return "Manter"

    resumo_df["Sugestao_Remocao"] = resumo_df.apply(_sugestao, axis=1)

    indicadores_invertidos = [k for k in alpha_result.keys if k.startswith("-")]

    print("\n   Métricas de Avaliação Calculadas.\n")

    return CorrelIndResult(
        contagem_na=cont_na,
        indicadores_na=indicadores_removidas_nas,
        correl=cor_result.cor_mat,
        p_value_cor=cor_result.p_mat,
        pcorrel=pcor_result.pcorrel,
        vif=vif_df,
        alpha_cronbach=alpha_result,
        indicadores_invertidos=indicadores_invertidos,
        resumo=resumo_df,
    )
