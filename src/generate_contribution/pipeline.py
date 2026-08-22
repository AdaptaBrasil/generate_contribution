"""Full end-to-end pipeline: treatment -> PPTX report (diagrams/maps included) ->
correlation/VIF/Cronbach diagnostics + figures.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import ReportConfig, TratamentoConfig
from .correlation import CorrelIndResult, correl_ind
from .figures import FigContNA, FigCorrelPlot, FigVIF, plotAlphaCronbach
from .pptx_report import slides_resultT
from .treatment import TreatmentResult, run_tratamento


@dataclass(slots=True)
class PipelineResult:
    treatment: TreatmentResult
    report_path: Path | None
    correl: CorrelIndResult | None


def run_pipeline(
    tratamento_config: TratamentoConfig,
    report_config: ReportConfig | None = None,
    figs_dir: Path = Path("FIGs"),
    run_report: bool = True,
    run_diagnostics: bool = True,
) -> PipelineResult:
    """Runs treatment, then optionally the PPTX report and the correlation/diagnostics figures."""
    treatment = run_tratamento(tratamento_config)

    report_path = None
    if run_report:
        if report_config is None:
            raise ValueError("report_config is required when run_report=True")
        report_path = slides_resultT(
            template=report_config.template,
            setor_estrategico=report_config.setor_estrategico,
            sigla=report_config.sigla,
            subsetor=report_config.subsetor,
            caminho_shp_mun=report_config.caminho_shp_mun,
            caminho_shp_uf=report_config.caminho_shp_uf,
            ind=report_config.ind,
            resu=report_config.resu,
            winz=report_config.winz,
            bxcx=report_config.bxcx,
            norm=report_config.norm,
            resumo=treatment.resumo,
            meta_adapta=treatment.imeta,
            reference=treatment.ref,
            databruto=treatment.dados_b,
            datawinz=treatment.data_win,
            databxcx=treatment.data_bxc,
            datanorm=treatment.data_normal,
            output_dir=report_config.output_dir,
        )

    correl = None
    if run_diagnostics:
        figs_dir = Path(figs_dir)
        correl = correl_ind(treatment.data_normal.idata)
        FigContNA(correl.contagem_na, figs_dir / "Contagem_NA_ISimples.png")
        FigCorrelPlot(correl.correl, tipo="Total", nfile=figs_dir / "Correlacao_Total.png")
        FigCorrelPlot(correl.pcorrel, tipo="Parcial", nfile=figs_dir / "Correlacao_Parcial.png")
        FigVIF(correl.vif, nfile=figs_dir / "VIF_ISimples.png")
        plotAlphaCronbach(correl.alpha_cronbach, nfile=figs_dir / "AlphaCronbach_ISimples.png")

    return PipelineResult(treatment=treatment, report_path=report_path, correl=correl)
