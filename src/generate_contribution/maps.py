"""Choropleth maps of one indicator across Brazilian municipalities.

Port of `Map_result` / `mapnorma_result` in `SCRIPTS/FUNCTION/F05_ADPGraficos.r`
(`sf`/`ggplot2::geom_sf` -> `geopandas` + `matplotlib`).
"""
from __future__ import annotations

from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch

_BRAZIL_XLIM = (-74.1, -34.5)
_BRAZIL_YLIM = (-35, 5)

_NORM_BREAKS = [0, 0.2, 0.4, 0.6, 0.8, 1]
_NORM_LABELS = ["0–0.2", "0.2–0.4", "0.4–0.6", "0.6–0.8", "0.8–1"]
_NORM_COLORS = ["#02c650", "#a9de00", "#ffcd00", "#ff8300", "#f40000"]


def load_shapefiles(caminho_shp_mun: str | Path, caminho_shp_uf: str | Path) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """Port of the `sf::st_transform(sf::st_read(...), crs = 4326)` calls in `slides_resultT`."""
    shp_mun = gpd.read_file(caminho_shp_mun).to_crs(epsg=4326)
    shp_uf = gpd.read_file(caminho_shp_uf).to_crs(epsg=4326)
    return shp_mun, shp_uf


def _merge_geo(shp_mun: gpd.GeoDataFrame, reference: pd.Series, dados: pd.Series, nome_col: str) -> gpd.GeoDataFrame:
    join_df = pd.DataFrame({"GEOCOD": reference.to_numpy(), nome_col: dados.to_numpy()})
    join_df["GEOCOD"] = pd.to_numeric(join_df["GEOCOD"], errors="coerce").astype("Int64")
    shp_mun = shp_mun.copy()
    shp_mun["CD_MUN"] = pd.to_numeric(shp_mun["CD_MUN"], errors="coerce").astype("Int64")
    return shp_mun.merge(join_df, left_on="CD_MUN", right_on="GEOCOD", how="inner")


def _finish_axes(ax: plt.Axes, titulo: str, fsize: float) -> None:
    ax.set_title(titulo, fontsize=1.5 * fsize)
    ax.set_xlim(*_BRAZIL_XLIM)
    ax.set_ylim(*_BRAZIL_YLIM)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_color("black")
        spine.set_linewidth(2)


def Map_result(
    inome: str,
    dados: pd.Series,
    reference: pd.Series,
    titulo: str = "Titulo",
    shp_mun: gpd.GeoDataFrame = None,
    shp_uf: gpd.GeoDataFrame = None,
    nome_arquivo: str | Path = "map_N7.png",
    largura: float = 20,
    altura: float = 24,
    dpi: float = 25,
    fsize: float = 16,
) -> None:
    """Port of `Map_result(...)`: continuous (Spectral) choropleth of raw/winsorized/Box-Cox values."""
    path = Path(nome_arquivo)
    path.parent.mkdir(parents=True, exist_ok=True)

    shp_0 = _merge_geo(shp_mun, reference, dados, inome)
    values = pd.to_numeric(shp_0[inome], errors="coerce")
    nbreaks = len(np.histogram_bin_edges(values.dropna(), bins="auto")) if values.notna().any() else 2

    fig, ax = plt.subplots(figsize=(largura, altura), dpi=dpi)
    shp_0.plot(column=inome, cmap="Spectral_r", ax=ax, edgecolor="none", legend=False)
    shp_uf.boundary.plot(ax=ax, color="black", linewidth=2)

    if values.notna().any():
        norm = plt.Normalize(vmin=values.min(), vmax=values.max())
        sm = plt.cm.ScalarMappable(cmap="Spectral_r", norm=norm)
        cbar = fig.colorbar(sm, ax=ax, fraction=0.04, pad=0.02, ticks=np.linspace(values.min(), values.max(), min(nbreaks, 10)))
        cbar.ax.tick_params(labelsize=fsize)

    _finish_axes(ax, titulo, fsize)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)


def mapnorma_result(
    inome: str,
    dados: pd.Series,
    reference: pd.Series,
    titulo: str = "Titulo",
    shp_mun: gpd.GeoDataFrame = None,
    shp_uf: gpd.GeoDataFrame = None,
    nome_arquivo: str | Path = "map_N7.png",
    largura: float = 20,
    altura: float = 24,
    dpi: float = 25,
    fsize: float = 16,
) -> None:
    """Port of `mapnorma_result(...)`: discrete 5-class choropleth for normalized [0,1] values."""
    path = Path(nome_arquivo)
    path.parent.mkdir(parents=True, exist_ok=True)

    shp_0 = _merge_geo(shp_mun, reference, dados, inome)
    values = pd.to_numeric(shp_0[inome], errors="coerce")
    classe = pd.cut(values, bins=_NORM_BREAKS, labels=_NORM_LABELS, include_lowest=True, right=True)
    shp_0 = shp_0.assign(classe=classe)

    cmap = ListedColormap(_NORM_COLORS)
    color_map = dict(zip(_NORM_LABELS, _NORM_COLORS))

    fig, ax = plt.subplots(figsize=(largura, altura), dpi=dpi)
    for label, color in color_map.items():
        subset = shp_0[shp_0["classe"] == label]
        if len(subset):
            subset.plot(ax=ax, color=color, edgecolor="none")
    shp_uf.boundary.plot(ax=ax, color="black", linewidth=2)

    handles = [Patch(facecolor=c, label=l) for l, c in color_map.items()]
    ax.legend(handles=handles, loc="lower left", fontsize=fsize, frameon=False, title_fontsize=fsize)

    _finish_axes(ax, titulo, fsize)
    fig.tight_layout()
    fig.savefig(path, facecolor="white")
    plt.close(fig)
