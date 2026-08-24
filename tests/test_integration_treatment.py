"""End-to-end integration test against the real vendored dataset
`DATASET/Base_inicial_SA_Acesso.xlsx`. Skipped automatically when that file
isn't present (e.g. a CI checkout that doesn't fetch the large binary
fixtures).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from generate_contribution.config import TratamentoConfig
from generate_contribution.correlation import correl_ind
from generate_contribution.treatment import run_tratamento

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_INPUT = _PROJECT_ROOT / "DATASET" / "Base_inicial_SA_Acesso.xlsx"

pytestmark = pytest.mark.skipif(not _INPUT.exists(), reason="requires the vendored DATASET/Base_inicial_SA_Acesso.xlsx")


def test_tratamento_and_correl_ind_on_real_dataset(tmp_path):
    config = TratamentoConfig(
        input=_INPUT,
        imeta_sheet="Metadados",
        idata_sheet="Dados_RA_Acesso",
        sigla="SA",
        subsetor="ACESSO",
        output_dir=tmp_path / "OUTPUT",
    )
    result = run_tratamento(config)

    assert result.output_paths[0].exists()
    assert result.output_paths[1].exists()
    assert result.dados_b.shape[0] == 5570

    correl = correl_ind(result.data_normal.idata)
    # columns with too many NAs to correlate reliably are excluded
    assert "QA" in correl.indicadores_na
    assert "MMPD" not in correl.indicadores_na
    assert 0 <= correl.alpha_cronbach.alpha_total <= 1
