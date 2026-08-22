"""Command-line entry point mirroring `AA01-INICIO_DESCRITIVO_INDICADORES.R`."""
from __future__ import annotations

import argparse
from pathlib import Path

from .config import ReportConfig, TratamentoConfig
from .pipeline import run_pipeline
from .treatment import run_tratamento


def _add_tratamento_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--input", required=True, type=Path, help="Input .xlsx workbook path.")
    p.add_argument("--imeta-sheet", default="Metadados")
    p.add_argument("--idata-sheet", required=True)
    p.add_argument("--method-boxcox", default="forecast", choices=["forecast", "yeojohnson"])
    p.add_argument("--sigla", default="SE")
    p.add_argument("--subsetor", default=None)
    p.add_argument("--output-dir", default=Path("OUTPUT"), type=Path)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="generate-contribution")
    sub = parser.add_subparsers(dest="command", required=True)

    tratamento = sub.add_parser(
        "tratamento", help="Run indicator treatment (winsorize/Box-Cox/normalize) and write the two output workbooks."
    )
    _add_tratamento_args(tratamento)

    pipeline = sub.add_parser(
        "pipeline",
        help="Full pipeline: treatment -> PPTX report (diagrams/maps) -> correlation/VIF/Cronbach diagnostics + figures.",
    )
    _add_tratamento_args(pipeline)
    pipeline.add_argument("--template", required=True, type=Path, help="PPTX template (e.g. TEMPLATE/ADAPTA_RESUMO.pptx).")
    pipeline.add_argument("--setor-estrategico", required=True)
    pipeline.add_argument("--shp-mun", required=True, type=Path, help="Municipality boundaries shapefile.")
    pipeline.add_argument("--shp-uf", required=True, type=Path, help="State boundaries shapefile.")
    pipeline.add_argument("--ind", type=int, default=None, help="Limit report to the first N indicators (default: all).")
    pipeline.add_argument("--figs-dir", default=Path("FIGs"), type=Path)
    pipeline.add_argument("--no-report", action="store_true", help="Skip PPTX report generation.")
    pipeline.add_argument("--no-diagnostics", action="store_true", help="Skip correlation/VIF/Cronbach diagnostics and figures.")

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "tratamento":
        config = TratamentoConfig(
            input=args.input,
            imeta_sheet=args.imeta_sheet,
            idata_sheet=args.idata_sheet,
            method_boxcox=args.method_boxcox,
            sigla=args.sigla,
            subsetor=args.subsetor,
            output_dir=args.output_dir,
        )
        run_tratamento(config)

    elif args.command == "pipeline":
        tratamento_config = TratamentoConfig(
            input=args.input,
            imeta_sheet=args.imeta_sheet,
            idata_sheet=args.idata_sheet,
            method_boxcox=args.method_boxcox,
            sigla=args.sigla,
            subsetor=args.subsetor,
            output_dir=args.output_dir,
        )
        report_config = ReportConfig(
            template=args.template,
            setor_estrategico=args.setor_estrategico,
            sigla=args.sigla,
            caminho_shp_mun=args.shp_mun,
            caminho_shp_uf=args.shp_uf,
            subsetor=args.subsetor,
            ind=args.ind,
            output_dir=args.output_dir,
        )
        run_pipeline(
            tratamento_config,
            report_config,
            figs_dir=args.figs_dir,
            run_report=not args.no_report,
            run_diagnostics=not args.no_diagnostics,
        )


if __name__ == "__main__":
    main()
