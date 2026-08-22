"""Configuration objects mirroring the parameters used across the R pipeline.

Equivalent to the arguments passed to `Tratamento()` (F07_ADP_GeraExcell.r) and
`slides_resultT()` (F06_ADPCriar_pptx_E01.R) in the original R script.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TratamentoConfig:
    """Mirrors the arguments of R's `Tratamento(input, iMeta, iData, method_boxcox, sigla, subsetor)`."""

    input: Path
    imeta_sheet: str = "Metadados"
    idata_sheet: str = "Dados"
    method_boxcox: str = "forecast"
    sigla: str = "SE"
    subsetor: str | None = None
    output_dir: Path = Path("OUTPUT")

    def __post_init__(self) -> None:
        self.input = Path(self.input)
        self.output_dir = Path(self.output_dir)


@dataclass(slots=True)
class ReportConfig:
    """Mirrors the arguments of R's `slides_resultT(...)`."""

    template: Path
    setor_estrategico: str
    sigla: str
    caminho_shp_mun: Path
    caminho_shp_uf: Path
    subsetor: str | None = None
    ind: int | None = None
    resu: bool = True
    winz: bool = True
    bxcx: bool = True
    norm: bool = True
    output_dir: Path = Path("OUTPUT")

    def __post_init__(self) -> None:
        self.template = Path(self.template)
        self.caminho_shp_mun = Path(self.caminho_shp_mun)
        self.caminho_shp_uf = Path(self.caminho_shp_uf)
        self.output_dir = Path(self.output_dir)
