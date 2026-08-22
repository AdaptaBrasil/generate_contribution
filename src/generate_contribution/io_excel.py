"""Excel I/O helpers: reading the input workbook and writing the two treatment output workbooks."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

from .config import TratamentoConfig


@dataclass(slots=True)
class InputData:
    imeta: pd.DataFrame
    idata: pd.DataFrame


def load_input(config: TratamentoConfig) -> InputData:
    """Read the Metadados and data sheets from the input workbook."""
    imeta = pd.read_excel(config.input, sheet_name=config.imeta_sheet)
    idata = pd.read_excel(config.input, sheet_name=config.idata_sheet)
    return InputData(imeta=imeta, idata=idata)


def _timestamp(fmt: str = "%Y-%m-%d_%Hh%Mm") -> str:
    return datetime.now().strftime(fmt)


def build_output_paths(config: TratamentoConfig) -> tuple[Path, Path]:
    """Builds the timestamped output filenames for the two treatment workbooks."""
    suffix = config.sigla + (config.subsetor or "")
    ts = _timestamp()
    config.output_dir.mkdir(parents=True, exist_ok=True)
    outfilex1 = config.output_dir / f"ANALISE_DESCRITIVA_{suffix}_{ts}.xlsx"
    outfilex2 = config.output_dir / f"DADOS_TRATADOS_{suffix}_{ts}.xlsx"
    return outfilex1, outfilex2


def write_descritiva_workbook(
    path: Path,
    resumo_total: pd.DataFrame,
    winsor_resumo: pd.DataFrame,
    boxcox_meta: pd.DataFrame,
) -> None:
    """Writes the ANALISE_DESCRITIVA_*.xlsx workbook (sheets: Descritivo, Winsorization, BoxCox)."""
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        resumo_total.to_excel(writer, sheet_name="Descritivo", index=False)
        winsor_resumo.to_excel(writer, sheet_name="Winsorization", index=False)
        boxcox_meta.to_excel(writer, sheet_name="BoxCox", index=False)


def write_dados_workbook(
    path: Path,
    data_ref: pd.DataFrame,
    idata_n7: pd.DataFrame,
    data_winsor: pd.DataFrame,
    data_boxcox: pd.DataFrame,
    data_normal: pd.DataFrame,
) -> None:
    """Writes the DADOS_TRATADOS_*.xlsx workbook.

    `data_ref` is the 4 reference columns (GEOCOD, MUN, UF, CLUSTER); each sheet
    below drops the CLUSTER column when concatenating.
    """
    ref_no_cluster = data_ref.drop(columns=[data_ref.columns[3]])
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.concat([ref_no_cluster, idata_n7], axis=1).to_excel(writer, sheet_name="BNivel 7", index=False)
        pd.concat([ref_no_cluster, data_winsor], axis=1).to_excel(writer, sheet_name="Winsorization", index=False)
        pd.concat([ref_no_cluster, data_boxcox], axis=1).to_excel(writer, sheet_name="BoxCox", index=False)
        pd.concat([ref_no_cluster, data_normal], axis=1).to_excel(writer, sheet_name="Normalizado", index=False)
