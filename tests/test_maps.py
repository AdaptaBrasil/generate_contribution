from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import box

from generate_contribution.maps import Map_result, mapnorma_result


def _synthetic_shapefiles() -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    # 4 small "municipalities" arranged in a 2x2 grid, 2 "states" (left/right halves)
    geocods = [1100015, 1100023, 1100031, 1100049]
    polys = [box(x, y, x + 1, y + 1) for x in (0, 1) for y in (0, 1)]
    shp_mun = gpd.GeoDataFrame({"CD_MUN": geocods}, geometry=polys, crs="EPSG:4326")

    uf_polys = [box(0, 0, 1, 2), box(1, 0, 2, 2)]
    shp_uf = gpd.GeoDataFrame({"UF": ["A", "B"]}, geometry=uf_polys, crs="EPSG:4326")
    return shp_mun, shp_uf


def test_map_result_writes_png(tmp_path):
    shp_mun, shp_uf = _synthetic_shapefiles()
    reference = pd.Series([1100015, 1100023, 1100031, 1100049])
    dados = pd.Series([10.0, 20.0, 30.0, 40.0])

    out = tmp_path / "map.png"
    Map_result("IND1", dados, reference, "Titulo", shp_mun, shp_uf, out, largura=4, altura=4, dpi=50, fsize=10)
    assert out.exists() and out.stat().st_size > 0


def test_mapnorma_result_writes_png(tmp_path):
    shp_mun, shp_uf = _synthetic_shapefiles()
    reference = pd.Series([1100015, 1100023, 1100031, 1100049])
    dados = pd.Series([0.05, 0.35, 0.65, 0.95])

    out = tmp_path / "mapnorma.png"
    mapnorma_result("IND1", dados, reference, "Titulo", shp_mun, shp_uf, out, largura=4, altura=4, dpi=50, fsize=10)
    assert out.exists() and out.stat().st_size > 0


def test_map_result_handles_string_vs_int_geocod_mismatch(tmp_path):
    shp_mun, shp_uf = _synthetic_shapefiles()
    shp_mun["CD_MUN"] = shp_mun["CD_MUN"].astype(str)  # simulate shapefile storing codes as text
    reference = pd.Series([1100015, 1100023, 1100031, 1100049])  # numeric, as read from Excel
    dados = pd.Series([1.0, 2.0, 3.0, 4.0])

    out = tmp_path / "map.png"
    Map_result("IND1", dados, reference, "Titulo", shp_mun, shp_uf, out, largura=4, altura=4, dpi=50, fsize=10)
    assert out.exists() and out.stat().st_size > 0
