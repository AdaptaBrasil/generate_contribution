from __future__ import annotations

import numpy as np
import pandas as pd

from generate_contribution.winsorise import ADPwinsorise, wins_par, winsorise1


def test_wins_par_clips_high_outlier():
    y = pd.Series([10.0, 11, 9, 10, 12, 8, 500.0])
    row = wins_par(y, "Numérico", "IND1")
    assert row["Aplicacao"] in {"A", "S", "I", "N"}
    assert row["LSUP"] < 500.0
    assert row["T_outlier"] >= 1


def test_wins_par_no_outliers_is_N():
    y = pd.Series([10.0, 10.0, 10.0, 10.0, 10.0])
    row = wins_par(y, "Numérico", "FLAT")
    assert row["Aplicacao"] == "N"
    assert row["T_outlier"] == 0


def test_adpwinsorise_handles_integer_dtype_columns(sample_idata, sample_imeta):
    idata_n7 = sample_idata[["IND1", "IND2"]].copy()
    idata_n7["IND2"] = np.arange(len(idata_n7), dtype="int64")  # an all-integer column, no NaN in the raw data
    imeta_n7 = sample_imeta[sample_imeta["Nivel"] == 7].reset_index(drop=True)

    result = ADPwinsorise(idata_n7, imeta_n7, sample_idata["CLUSTER"])
    assert result.idata["IND2"].notna().all()


def test_adpwinsorise_clips_outlier_within_range(sample_idata, sample_imeta):
    idata_n7 = sample_idata[["IND1", "IND2"]]
    imeta_n7 = sample_imeta[sample_imeta["Nivel"] == 7].reset_index(drop=True)
    result = ADPwinsorise(idata_n7, imeta_n7, sample_idata["CLUSTER"])
    assert set(result.resumo["iName"]) == {"IND1", "IND2"}
    # the injected 500.0 outlier in IND1 must be clipped down
    assert result.idata["IND1"].max() < 500.0
    # NaNs in IND2 must be preserved, not silently dropped or zeroed
    assert result.idata["IND2"].isna().sum() == idata_n7["IND2"].isna().sum()


def _imeta_with_cluster_column(sample_imeta: pd.DataFrame) -> pd.DataFrame:
    imeta_with_cluster = sample_imeta.copy()
    imeta_with_cluster.loc[len(imeta_with_cluster)] = dict(
        N=7, Nivel=7, Code="CLU1", Nome="Cluster indicator", Tipo="Indicator", Pai="PP", Classe="Cluster"
    )
    return imeta_with_cluster[imeta_with_cluster["Nivel"] == 7].reset_index(drop=True)


def test_winsorise1_grupo_rows_only_for_cluster_columns(sample_idata, sample_imeta):
    imeta_n7 = _imeta_with_cluster_column(sample_imeta)
    cluster = sample_idata["CLUSTER"]
    idata_n7 = sample_idata[["IND1", "IND2"]].copy()
    idata_n7["CLU1"] = np.where(cluster == 1, 5.0, 15.0)

    resumo = winsorise1(idata_n7, imeta_n7, cluster)

    ind_rows = resumo[resumo["iName"].isin(["IND1", "IND2"])]
    assert set(ind_rows["Classe"]) == {"Numérico"}  # no spurious Grupo 1/2 rows for plain Numérico columns

    clu_rows = resumo[resumo["iName"] == "CLU1"]
    assert set(clu_rows["Classe"]) == {"Grupo 1", "Grupo 2"}  # no "Numérico" row for a Cluster column


def test_adpwinsorise_merges_group_clips_instead_of_overwriting(sample_idata, sample_imeta):
    imeta_n7 = _imeta_with_cluster_column(sample_imeta)
    cluster = sample_idata["CLUSTER"].reset_index(drop=True)
    n = len(cluster)

    clu1 = np.where(cluster == 1, 10.0, 20.0).astype(float)
    # inject an outlier into EACH group so both group-specific clips must survive
    first_g1_idx = cluster[cluster == 1].index[0]
    first_g2_idx = cluster[cluster == 2].index[0]
    clu1[first_g1_idx] = 9999.0
    clu1[first_g2_idx] = -9999.0

    idata_n7 = sample_idata[["IND1", "IND2"]].reset_index(drop=True).copy()
    idata_n7["CLU1"] = clu1

    result = ADPwinsorise(idata_n7, imeta_n7, cluster)
    out = result.idata["CLU1"]

    assert out[first_g1_idx] < 9999.0  # Grupo 1's clip took effect on its own subset
    assert out[first_g2_idx] > -9999.0  # Grupo 2's clip took effect on its own subset, not just the last-applied one
    # untouched (non-outlier) values in both groups must be unchanged
    assert out[cluster == 1].drop(index=first_g1_idx).eq(10.0).all()
    assert out[cluster == 2].drop(index=first_g2_idx).eq(20.0).all()


def test_adpwinsorise_passes_through_descricao_and_score_columns(sample_idata, sample_imeta):
    imeta = sample_imeta.copy()
    imeta.loc[len(imeta)] = dict(N=7, Nivel=7, Code="SCOREX", Nome="Score col", Tipo="Indicator", Pai="PP", Classe="Score")
    imeta_n7 = imeta[imeta["Nivel"] == 7].reset_index(drop=True)

    idata_n7 = sample_idata[["IND1", "IND2"]].copy()
    idata_n7["SCOREX"] = np.arange(len(idata_n7), dtype=float)

    result = ADPwinsorise(idata_n7, imeta_n7, sample_idata["CLUSTER"])
    pd.testing.assert_series_equal(
        result.idata["SCOREX"].reset_index(drop=True), idata_n7["SCOREX"].reset_index(drop=True)
    )
