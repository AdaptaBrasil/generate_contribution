from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def sample_imeta() -> pd.DataFrame:
    return pd.DataFrame(
        [
            dict(N=1, Nivel=0, Code="GEOCOD", Nome="Geocodigo", Tipo="Referencia", Pai="REF", Classe="Descricao"),
            dict(N=2, Nivel=0, Code="MUN", Nome="Municipio", Tipo="Referencia", Pai="REF", Classe="Descricao"),
            dict(N=3, Nivel=0, Code="UF", Nome="UF", Tipo="Referencia", Pai="REF", Classe="Descricao"),
            dict(N=4, Nivel=0, Code="CLUSTER", Nome="Cluster", Tipo="Referencia", Pai="REF", Classe="Descricao"),
            dict(N=5, Nivel=7, Code="IND1", Nome="Indicador 1", Tipo="Indicator", Pai="PP", Classe="Numérico"),
            dict(N=6, Nivel=7, Code="IND2", Nome="Indicador 2", Tipo="Indicator", Pai="PP", Classe="Numérico"),
        ]
    )


@pytest.fixture
def sample_idata() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    n = 60
    ind1 = rng.normal(loc=10, scale=2, size=n)
    ind1[0] = 500.0  # obvious high outlier
    ind2 = rng.uniform(low=1, high=5, size=n)
    ind2[[3, 7]] = np.nan
    return pd.DataFrame(
        {
            "GEOCOD": np.arange(1100000, 1100000 + n),
            "MUN": [f"Municipio {i}" for i in range(n)],
            "UF": ["RO"] * n,
            "CLUSTER": rng.integers(1, 3, size=n),
            "IND1": ind1,
            "IND2": ind2,
        }
    )
