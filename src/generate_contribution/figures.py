"""Static diagnostic and per-indicator figures.

Port of the plotting functions in `SCRIPTS/FUNCTION/F08_ADPCORREL.r`
(`FigContNA`, `FigCorrelPlot`, `FigVIF`, `plotAlphaCronbach`) and
`SCRIPTS/FUNCTION/F05_ADPGraficos.r` (`criar_grafico`, `grafico_final`).

Library mapping: `ggplot2`/`corrplot` -> `matplotlib`. Colors, thresholds and
axis ranges are carried over as literal constants from the R source.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from scipy import stats as sp_stats

from .correlation import ADPAlphaCronResult

# R color names -> hex (matplotlib doesn't know "sienna1"/"firebrick" as R defines them)
_CORRPLOT_CMAP = LinearSegmentedColormap.from_list(
    "corrplot_beige_firebrick", ["#F5F5DC", "#F5F5DC", "#FF8247", "#B22222"]
)


def _ensure_parent(nfile: str | Path) -> Path:
    path = Path(nfile)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def FigContNA(y: pd.Series, nfile: str | Path = "TESTE.png") -> None:
    """Port of `FigContNA(Y, nfile)`: bar chart of NA counts per indicator."""
    path = _ensure_parent(nfile)
    fig, ax = plt.subplots(figsize=(10, 6), dpi=600)
    ax.bar(y.index.astype(str), y.to_numpy(), color="steelblue")
    ax.set_title("Total de NA's por Indicador Simples", fontsize=16, fontweight="bold")
    ax.set_xlabel("Indicadores Simples", fontsize=14, fontweight="bold")
    ax.set_ylabel("Número de NA's", fontsize=14, fontweight="bold")
    ax.set_ylim(0, 6000)
    ax.set_yticks(np.arange(0, 6001, 1000))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10)
    plt.setp(ax.get_yticklabels(), fontsize=12)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print("\n       Figura de Contagem de NA's Gerada\n")


def FigCorrelPlot(y: pd.DataFrame, tipo: str = "Total", nfile: str | Path = "output.png") -> None:
    """Port of `FigCorrelPlot(Y, tipo, nfile)`: circle correlogram (lower/upper triangle)."""
    path = _ensure_parent(nfile)
    cols = list(y.columns)
    n = len(cols)
    fig, ax = plt.subplots(figsize=(2000 / 300, 2000 / 300), dpi=300)

    for i in range(n):  # row
        for j in range(n):  # col
            visible = (j <= i) if tipo == "Total" else (j >= i)
            if not visible:
                continue
            value = float(y.iloc[i, j])
            color = _CORRPLOT_CMAP(np.clip(value, 0, 1))
            size = 20 + 260 * np.clip(value, 0, 1)
            ax.scatter(j, n - 1 - i, s=size, color=color, edgecolors="none")

    ax.set_xlim(-0.5, n - 0.5)
    ax.set_ylim(-0.5, n - 0.5)
    ax.set_xticks(range(n))
    ax.set_xticklabels(cols, rotation=90, fontsize=6.5, color="black")
    ax.set_yticks(range(n))
    ax.set_yticklabels(list(reversed(cols)), fontsize=6.5, color="black")
    ax.set_aspect("equal")
    ax.set_title(f"Correlação {tipo} entre Indicadores Simples", fontsize=11, pad=14)
    ax.set_ylabel("Indicadores Simples", fontsize=9)

    sm = plt.cm.ScalarMappable(cmap=_CORRPLOT_CMAP, norm=plt.Normalize(0, 1))
    fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)

    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"\n       Figura de Correlação ({tipo}) Gerada.\n")


def FigVIF(y: pd.DataFrame, nfile: str | Path = "TESTE.png") -> None:
    """Port of `FigVIF(Y, nfile)`: VIF lollipop chart with 5/10 reference lines."""
    path = _ensure_parent(nfile)
    variavel = y.iloc[:, 0].astype(str)
    vif = y.iloc[:, 1].astype(float)

    fig, ax = plt.subplots(figsize=(10, 6), dpi=600)
    ax.vlines(variavel, 0, vif, linewidth=1.5, color="black")
    ax.scatter(variavel, vif, color="blue", s=60, zorder=3)
    ax.axhline(5, linestyle="--", color="blue", linewidth=1)
    ax.axhline(10, linestyle="--", color="red", linewidth=1.2)
    ax.set_ylim(0, 15)
    ax.set_title("Fatores de Inflação de Variância - VIF", fontsize=16, fontweight="bold")
    ax.set_xlabel("Indicadores Simples", fontsize=14, fontweight="bold")
    ax.set_ylabel("VIF", fontsize=14, fontweight="bold")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=10, fontweight="bold")
    plt.setp(ax.get_yticklabels(), fontsize=12)
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"\n    Figura VIF \n  {path}\n ")


_ALPHA_FILL_COLORS = {
    "Remover": "#bd0a0aff",
    "Remover (invertido)": "#F8BDBD",
    "Manter": "#0f09ccff",
    "Manter (invertido)": "#919ee8ff",
}


def plotAlphaCronbach(alpha_result: ADPAlphaCronResult, nfile: str | Path = "output.png") -> None:
    """Port of `plotAlphaCronbach(alpha_df, alpha_total, nfile)`."""
    path = _ensure_parent(nfile)
    alpha_total = alpha_result.alpha_total
    invertido = {name.lstrip("-") for name in alpha_result.keys if name.startswith("-")}

    df = alpha_result.alpha_df.copy()
    df["Invertido"] = df["Indicador"].isin(invertido)
    df["Grupo"] = np.where(df["Alpha_if_Dropped"] > alpha_total, "Remover", "Manter")
    df["GrupoExibicao"] = np.where(
        df["Invertido"], df["Grupo"] + " (invertido)", df["Grupo"]
    )
    df["Label"] = np.where(df["Invertido"], df["Indicador"] + "*", df["Indicador"])

    fig, ax = plt.subplots(figsize=(10, 6), dpi=600)
    colors = [_ALPHA_FILL_COLORS[g] for g in df["GrupoExibicao"]]
    ax.bar(df["Label"], df["Alpha_if_Dropped"], color=colors, width=0.7)
    ax.axhline(alpha_total, linestyle="--", color="black")
    ax.set_ylim(0, max(1.2 * round(alpha_total, 1), 0.1))
    ax.set_title(f"Impacto no Alpha de Cronbach (α = {round(alpha_total, 3)})", fontsize=15, fontweight="bold")
    ax.set_xlabel("Indicadores (* indica inversão automática)", fontsize=12)
    ax.set_ylabel("Alpha se removido", fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")

    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in _ALPHA_FILL_COLORS.values()]
    ax.legend(handles, list(_ALPHA_FILL_COLORS.keys()), title="Sugestão de ação", loc="best", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"\n    Figura Alpha de Cronbach \n  {path}\n ")


def criar_grafico(
    dados: pd.Series,
    nome_arquivo: str | Path = "grafico_combinado.png",
    largura: float = 10,
    altura: float = 5,
    dpi: float = 25,
    nvalores: str = "DD1",
    fsize: float = 16,
) -> None:
    """Port of `criar_grafico`: side-by-side boxplot + histogram-with-normal-curve for one indicator."""
    path = _ensure_parent(nome_arquivo)
    values = pd.to_numeric(dados, errors="coerce").dropna().to_numpy()

    fig, (ax_hist, ax_box) = plt.subplots(1, 2, figsize=(largura, altura), dpi=dpi, gridspec_kw={"width_ratios": [2, 1.2]})

    ax_box.boxplot(values, patch_artist=True, boxprops=dict(facecolor="lightblue", color="blue"))
    ax_box.set_xticks([])
    ax_box.set_ylabel("Valores", fontsize=fsize)
    ax_box.set_xlabel(nvalores, fontsize=fsize)
    ax_box.set_title("Boxplot", fontsize=fsize, fontweight="bold")
    for spine in ax_box.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)

    if len(values) > 0 and np.nanstd(values) > 0:
        counts, bin_edges = np.histogram(values, bins="sturges")
        ax_hist.hist(values, bins=bin_edges, density=True, color="lightblue", edgecolor="blue")
        mu, sigma = np.mean(values), np.std(values)
        xs = np.linspace(bin_edges[0], bin_edges[-1], 200)
        ax_hist.plot(xs, sp_stats.norm.pdf(xs, mu, sigma), color="red", linewidth=1.5)
    ax_hist.set_xlabel(nvalores, fontsize=fsize)
    ax_hist.set_ylabel("Densidade", fontsize=fsize)
    ax_hist.set_title("Histograma com Distribuição Normal", fontsize=fsize, fontweight="bold")
    for spine in ax_hist.spines.values():
        spine.set_visible(True)
        spine.set_linewidth(2)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def grafico_final(
    df1: pd.DataFrame,
    df: pd.DataFrame,
    nome_arquivo: str | Path = "grafico_combinado.png",
    largura: float = 10,
    altura: float = 5,
    dpi: float = 25,
    nvalores: str = "nvalores",
    fsize: float = 16,
) -> None:
    """Port of `grafico_final`: scatter (normalized vs raw) + histogram of normalized values."""
    path = _ensure_parent(nome_arquivo)
    fig, (ax_hist, ax_scatter) = plt.subplots(1, 2, figsize=(largura, altura), dpi=dpi)

    try:
        values = pd.to_numeric(df.iloc[:, 0], errors="coerce").dropna().to_numpy()
        if len(values) == 0 or np.nanstd(values) == 0:
            raise ValueError("insufficient variation to plot histogram")
        counts, bin_edges = np.histogram(values, bins="sturges")
        ax_hist.hist(values, bins=bin_edges, density=True, color="lightblue", edgecolor="blue")
        mu, sigma = np.mean(values), np.std(values)
        xs = np.linspace(bin_edges[0], bin_edges[-1], 200)
        ax_hist.plot(xs, sp_stats.norm.pdf(xs, mu, sigma), color="red", linewidth=1.5)
        ax_hist.set_xlabel(nvalores, fontsize=fsize)
        ax_hist.set_ylabel("Densidade", fontsize=fsize)
        ax_hist.set_title(f"Histograma dados Normalizados - {nvalores}", fontsize=fsize, fontweight="bold")
    except Exception as e:  # pragma: no cover - mirrors the R tryCatch fallback
        ax_hist.axis("off")
        ax_hist.text(0.5, 0.5, f"Erro ao gerar gráfico:\n{e}", ha="center", va="center", color="red", fontsize=fsize * 0.6)
        ax_hist.set_title(f"Histograma dados Normalizados - {nvalores}", fontsize=fsize, fontweight="bold")

    ax_scatter.scatter(df1["Normalizado"], df1["N_Normalizado"], color="blue")
    ax_scatter.set_xlabel("Dados Normalizados", fontsize=fsize)
    ax_scatter.set_ylabel("Dados Brutos", fontsize=fsize)
    ax_scatter.set_title(f"Gráfico de Dispersão - {nvalores}", fontsize=fsize, fontweight="bold")
    for ax in (ax_hist, ax_scatter):
        for spine in ax.spines.values():
            spine.set_visible(True)
            spine.set_linewidth(2)

    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
