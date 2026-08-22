"""End-to-end indicator treatment pipeline.

Port of `SCRIPTS/FUNCTION/F07_ADP_GeraExcell.r` (`Tratamento`): loads the input
workbook, runs descriptive stats -> winsorization -> Box-Cox -> normalization,
and writes the two output workbooks.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .boxcox import ADPBoxCox, BoxCoxResult
from .config import TratamentoConfig
from .io_excel import (
    build_output_paths,
    load_input,
    write_dados_workbook,
    write_descritiva_workbook,
)
from .normalise import ADPNormalise, NormaliseResult
from .resumo import ADPresumo, ResumoResult
from .winsorise import ADPwinsorise, WinsoriseResult


@dataclass(slots=True)
class TreatmentResult:
    ref: pd.DataFrame
    resumo: ResumoResult
    imeta: pd.DataFrame
    dados_b: pd.DataFrame
    data_win: WinsoriseResult
    data_bxc: BoxCoxResult
    data_normal: NormaliseResult
    output_paths: tuple[Path, Path]


def run_tratamento(config: TratamentoConfig) -> TreatmentResult:
    """Port of `Tratamento(input, iMeta, iData, method_boxcox, sigla, subsetor)`."""
    raw = load_input(config)
    imeta_adapta = raw.imeta
    idata_bruto = raw.idata

    imeta_n7 = imeta_adapta[imeta_adapta["Nivel"] == 7].reset_index(drop=True)
    data_ref = idata_bruto.iloc[:, 0:4].reset_index(drop=True)
    idata_n7 = idata_bruto.iloc[:, 4:].reset_index(drop=True).round(2)

    resumo = ADPresumo(idata_n7, list(imeta_n7["Classe"]), data_ref.iloc[:, 3], list(idata_n7.columns))

    data_winsor = ADPwinsorise(idata_n7, imeta_n7, data_ref.iloc[:, 3])

    data_bxcx = ADPBoxCox(
        data_winsor.idata,
        idata_n7,
        list(imeta_n7["Classe"]),
        data_ref.iloc[:, 3],
        list(idata_n7.columns),
        config.method_boxcox,
    )
    data_normal = ADPNormalise(data_bxcx.data)

    outfilex1, outfilex2 = build_output_paths(config)
    write_descritiva_workbook(outfilex1, resumo.resumo_total, data_winsor.resumo, data_bxcx.meta)
    write_dados_workbook(outfilex2, data_ref, idata_n7, data_winsor.idata, data_bxcx.data, data_normal.idata)
    print(f"\n Arquivos .xlsx Gerados \n  {outfilex1}\n  {outfilex2}\n")

    return TreatmentResult(
        ref=data_ref,
        resumo=resumo,
        imeta=imeta_n7,
        dados_b=idata_n7,
        data_win=data_winsor,
        data_bxc=data_bxcx,
        data_normal=data_normal,
        output_paths=(outfilex1, outfilex2),
    )
