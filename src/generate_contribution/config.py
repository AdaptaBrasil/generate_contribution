"""Configuration objects for the treatment and reporting pipeline.

`TratamentoConfig` holds the parameters for `treatment.run_tratamento`;
`ReportConfig` holds the parameters for `pptx_report.slides_resultT`.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TratamentoConfig:
    """Parameters for `run_tratamento`: input workbook, metadata/data sheet names, and output naming."""

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
    """Parameters for `slides_resultT`: PPTX template, shapefiles, and which report stages to run."""

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
