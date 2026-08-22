from __future__ import annotations

import numpy as np
import pandas as pd

from generate_contribution.resumo import ADPresumo, boxplot_stats, criar_resumo, fivenum


def test_fivenum_matches_known_r_example():
    # R: fivenum(c(1,2,3,4,5,6,7,8,9,10)) -> 1.0 3.0 5.5 8.0 10.0
    x = np.arange(1, 11, dtype=float)
    stats = fivenum(x)
    np.testing.assert_allclose(stats, [1.0, 3.0, 5.5, 8.0, 10.0])


def test_boxplot_stats_flags_outlier():
    x = np.array([10.0, 11, 9, 10, 12, 8, 500.0])
    stats, out = boxplot_stats(x)
    assert 500.0 in out
    assert stats[4] < 500.0  # upper whisker excludes the outlier


def test_criar_resumo_numerico_shape():
    data = pd.Series([1.0, 2.0, 3.0, 4.0, np.nan])
    res = criar_resumo(data, "Numérico", None, "IND1")
    assert list(res["iName"]) == ["IND1"]
    assert res.loc[0, "NAs"] == 1
    assert res.loc[0, "Classe"] == "Numérico"


def test_criar_resumo_score_all_dash_ready():
    data = pd.Series([np.nan] * 5)
    res = criar_resumo(data, "Score", None, "SCOREX")
    assert res.loc[0, "Classe"] == "Score"
    assert pd.isna(res.loc[0, "Min"])


def test_criar_resumo_cluster_uses_group_subset_not_full_data():
    # group 1 is centered around 0, group 2 around 100 -> medians must differ per group
    data = pd.Series([0.0, 0.0, 0.0, 0.0, 100.0, 100.0, 100.0, 100.0])
    cluster = pd.Series([1, 1, 1, 1, 2, 2, 2, 2])
    res = criar_resumo(data, "Cluster", cluster, "CLU1").set_index("Classe")

    assert res.loc["Grupo 1", "Mediana"] == 0.0
    assert res.loc["Grupo 2", "Mediana"] == 100.0
    assert res.loc["Grupo 1", "Max"] == 0.0
    assert res.loc["Grupo 2", "Min"] == 100.0
    assert res.loc["Conjunto Completo", "Mediana"] == 50.0


def test_adpresumo_basico_and_na_views(sample_idata):
    data = sample_idata[["IND1", "IND2"]]
    result = ADPresumo(data, ["Numérico", "Numérico"], sample_idata["CLUSTER"], ["IND1", "IND2"])
    assert list(result.resumo_basico.columns) == ["IND1", "IND2"]
    assert list(result.resumo_basico.index) == [
        "Classe",
        "Min",
        "Quartil 1",
        "Mediana",
        "Quartil 3",
        "Max",
        "Outliers_Per",
    ]
    assert list(result.resumo_na.columns) == ["iName", "NAs", "Percentual_NAs", "Valores_Unicos", "Percentual_Unicos"]
    # IND2 has 2 NAs injected in the fixture
    assert result.resumo_na.loc[result.resumo_na["iName"] == "IND2", "NAs"].iloc[0] == 2
