"""Descriptive statistics summaries: per-indicator (and per-cluster-group) boxplot
stats, NA counts, and unique-value counts, combined into the tables used by the
treatment output workbook and the PPTX report.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np
import pandas as pd

_COLUMNS = [
    "iName",
    "Classe",
    "Min",
    "Quartil 1",
    "Mediana",
    "Quartil 3",
    "Max",
    "Outliers_Per",
    "NAs",
    "Percentual_NAs",
    "Valores_Unicos",
    "Percentual_Unicos",
]


def fivenum(x: np.ndarray) -> np.ndarray:
    """Tukey's five-number summary: [min, lower hinge, median, upper hinge, max].

    `x` must already be NA-free.
    """
    x = np.sort(np.asarray(x, dtype=float))
    n = len(x)
    if n == 0:
        return np.full(5, np.nan)
    n4 = np.floor((n + 3) / 2) / 2
    d = np.array([1, n4, (n + 1) / 2, n + 1 - n4, n])
    lo = np.floor(d).astype(int) - 1
    hi = np.ceil(d).astype(int) - 1
    return 0.5 * (x[lo] + x[hi])


def boxplot_stats(x: np.ndarray, coef: float = 1.5) -> tuple[np.ndarray, np.ndarray]:
    """Tukey boxplot statistics. Returns (stats[5], outlier_values).

    stats = [lower whisker, Q1 (lower hinge), median, Q3 (upper hinge), upper whisker].
    """
    x = np.asarray(x, dtype=float)
    xn = x[~np.isnan(x)]
    stats = fivenum(xn)
    if len(xn) == 0 or np.isnan(stats[1]) or np.isnan(stats[3]):
        return stats, np.array([])
    iqr = stats[3] - stats[1]
    if coef == 0:
        return stats, np.array([])
    out_mask = (xn < stats[1] - coef * iqr) | (xn > stats[3] + coef * iqr)
    if out_mask.any():
        stats = stats.copy()
        stats[0] = xn[~out_mask].min()
        stats[4] = xn[~out_mask].max()
    return stats, xn[out_mask]


def _r2(value: float) -> float:
    return round(float(value), 2)


def criar_resumo(
    data: pd.Series,
    class_type: str,
    cluster: pd.Series | None,
    name: str,
) -> pd.DataFrame:
    """Descriptive summary row(s) for one indicator column.

    Numérico columns get a single row; Cluster columns get one row per
    cluster group plus an overall "Conjunto Completo" row; Score/Descricao
    columns get a single placeholder row (no numeric stats apply).
    """
    data = pd.Series(data)
    n = len(data)
    na_count = int(data.isna().sum())
    na_percent = _r2(na_count / n * 100) if n else np.nan
    non_na = data.dropna()
    unique_count = int(non_na.nunique())
    unique_percent = _r2(unique_count / len(non_na) * 100) if len(non_na) else np.nan

    rows: list[dict] = []

    if class_type == "Numérico":
        stats, out = boxplot_stats(data.to_numpy())
        per_out = _r2(len(out) / n * 100) if n else np.nan
        rows.append(
            dict(
                zip(
                    _COLUMNS,
                    [
                        name,
                        "Numérico",
                        _r2(stats[0]),
                        _r2(stats[1]),
                        _r2(stats[2]),
                        _r2(stats[3]),
                        _r2(stats[4]),
                        per_out,
                        na_count,
                        na_percent,
                        unique_count,
                        unique_percent,
                    ],
                )
            )
        )
    elif class_type == "Cluster":
        if cluster is None:
            raise ValueError("Cluster information must be provided for 'Cluster' class type.")
        cluster = pd.Series(cluster).reset_index(drop=True)
        data_r = data.reset_index(drop=True)

        for cl in pd.unique(cluster):
            mask = cluster == cl
            group_data = data_r[mask]
            group_non_na = group_data.dropna()
            group_stats, group_out = boxplot_stats(group_data.to_numpy())
            group_per_out = _r2(len(group_out) / len(group_data) * 100) if len(group_data) else np.nan
            group_na = int(group_data.isna().sum())
            group_na_pct = _r2(group_na / len(group_data) * 100) if len(group_data) else np.nan
            group_unique = int(group_non_na.nunique())
            group_unique_pct = _r2(group_unique / len(group_non_na) * 100) if len(group_non_na) else np.nan
            rows.append(
                dict(
                    zip(
                        _COLUMNS,
                        [
                            name,
                            f"Grupo {cl}",
                            _r2(group_stats[0]),
                            _r2(group_stats[1]),
                            _r2(group_stats[2]),
                            _r2(group_stats[3]),
                            _r2(group_stats[4]),
                            group_per_out,
                            group_na,
                            group_na_pct,
                            group_unique,
                            group_unique_pct,
                        ],
                    )
                )
            )

        full_out_stats, full_out = boxplot_stats(data_r.to_numpy())
        full_row = dict(
            zip(
                _COLUMNS,
                [
                    name,
                    "Conjunto Completo",
                    _r2(np.nanmin(data_r)) if n else np.nan,
                    _r2(np.nanquantile(data_r, 0.25)) if n else np.nan,
                    _r2(np.nanmedian(data_r)) if n else np.nan,
                    _r2(np.nanquantile(data_r, 0.75)) if n else np.nan,
                    _r2(np.nanmax(data_r)) if n else np.nan,
                    _r2(len(full_out) / n * 100) if n else np.nan,
                    na_count,
                    na_percent,
                    unique_count,
                    unique_percent,
                ],
            )
        )
        rows = [full_row] + rows
    else:
        rows.append(
            dict(
                zip(
                    _COLUMNS,
                    [name, "Score", np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan, np.nan],
                )
            )
        )

    return pd.DataFrame(rows, columns=_COLUMNS)


@dataclass(slots=True)
class ResumoResult:
    resumo_total: pd.DataFrame
    resumo_basico: pd.DataFrame
    resumo_na: pd.DataFrame


def ADPresumo(
    data: pd.DataFrame,
    class_types: Sequence[str],
    cluster: pd.Series | None,
    names: Sequence[str],
) -> ResumoResult:
    """Combines `criar_resumo` for every column into the three summary views used downstream:
    the full table, a transposed "basico" view (one column per indicator/group), and the
    NA/uniqueness-only view.
    """
    if data.shape[1] != len(class_types) or data.shape[1] != len(names):
        raise ValueError("Number of columns in data must match the length of class_types and names.")

    parts = [
        criar_resumo(data.iloc[:, i], class_types[i], cluster, names[i])
        for i in range(data.shape[1])
    ]
    resumo_combinado = pd.concat(parts, ignore_index=True)

    # Every NA is displayed as "-" (which coerces the table to strings) so
    # downstream slide tables show a dash instead of a blank cell.
    display = resumo_combinado.astype(object).where(resumo_combinado.notna(), "-")

    resumo_basico = display.set_index("iName").loc[:, "Classe":"Outliers_Per"].T
    resumo_basico.columns = display["iName"].to_numpy()

    resumo_na = display[["iName", "NAs", "Percentual_NAs", "Valores_Unicos", "Percentual_Unicos"]]

    return ResumoResult(resumo_total=display, resumo_basico=resumo_basico, resumo_na=resumo_na)
