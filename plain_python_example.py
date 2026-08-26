"""Python equivalent of ScriptRCalculoContribuicao/SCRIPTS/AA01-INICIO_DESCRITIVO_INDICADORES.R.

Runs the full pipeline (treatment -> PPTX report -> correlation/VIF/Cronbach diagnostics
and figures) against DATASET/Base_inicial_SA_Acesso.xlsx, mirroring the parameters the
R script passed to Tratamento(...) and slides_resultT(...).
"""
from __future__ import annotations

from pathlib import Path

from generate_contribution.config import ReportConfig, TratamentoConfig
from generate_contribution.pipeline import run_pipeline

BASE_DIR = Path(__file__).resolve().parent

tratamento_config = TratamentoConfig(
    input=BASE_DIR / "DATASET" / "Base_inicial_SA_Acesso.xlsx",
    imeta_sheet="Metadados",
    idata_sheet="Dados_RA_Acesso",
    method_boxcox="forecast",
    sigla="SA",
    subsetor="ACESSO",
    output_dir=BASE_DIR / "OUTPUT",
)

report_config = ReportConfig(
    template=BASE_DIR / "TEMPLATE" / "ADAPTA_RESUMO.pptx",
    setor_estrategico="Segurança Alimentar",
    sigla="SA",
    subsetor="ACESSO",
    caminho_shp_mun=BASE_DIR / "DATASET" / "SHP" / "BR_Municipios_2022_gr.shp",
    caminho_shp_uf=BASE_DIR / "DATASET" / "SHP" / "BR_UF_2022_gr.shp",
    ind=None,
    resu=True,
    winz=True,
    bxcx=True,
    norm=True,
    output_dir=BASE_DIR / "OUTPUT",
)

if __name__ == "__main__":
    run_pipeline(
        tratamento_config,
        report_config,
        figs_dir=BASE_DIR / "FIGs",
        run_report=True,
        run_diagnostics=True,
    )
