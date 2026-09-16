from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.analytics_core.runner import generate_report as core_generate_report
from src.builder.analytic_db_builder import build_analytic_database
from src.contracts.vocabulary import ExecutionMode
from src.reporter.tabulator import ReportResult
from src.reporter.tabulator import generate_report as legacy_generate_report


class Metadata:
    variable_value_labels = {
        "Q1": {1: "Sí", 2: "No"},
        "SEGMENTO": {1: "Norte", 2: "Sur"},
    }
    variable_labels = {
        "Q1": "Pregunta principal",
        "SEGMENTO": "Segmento",
    }


def assert_report_parity(
    test_case: unittest.TestCase,
    left: ReportResult,
    right: ReportResult,
) -> None:
    for field in (
        "question_id",
        "title",
        "question_type",
        "calculation",
        "calculations",
        "base",
        "banner",
        "banners",
        "filters",
        "filter_summary",
        "ponderador",
        "confidence",
        "significance_display",
        "warnings",
        "base_before_filters",
        "banner_mode",
    ):
        test_case.assertEqual(
            getattr(left, field),
            getattr(right, field),
            field,
        )
    pd.testing.assert_frame_equal(left.table, right.table)
    pd.testing.assert_frame_equal(left.summary, right.summary)
    pd.testing.assert_frame_equal(left.significance, right.significance)
    for key in sorted(set(left.summaries) | set(right.summaries)):
        pd.testing.assert_frame_equal(left.summaries[key], right.summaries[key])


class CoreWrapperParityTests(unittest.TestCase):
    def test_core_wrapper_delegates_without_changing_report_content(self) -> None:
        df_spss = pd.DataFrame(
            {
                "Q1": [1, 2, 1, 2, 1, 2],
                "SEGMENTO": [1, 1, 2, 2, 1, 2],
                "POND": [1.0, 1.5, 0.5, 2.0, 1.0, 1.0],
            }
        )
        datamap = pd.DataFrame(
            [
                {
                    "variable": "Q1",
                    "pregunta_id": "Q1",
                    "texto_pregunta": "Pregunta principal",
                    "tipo_pregunta": "RU",
                    "clasificacion_analitica": "Pregunta analizable",
                    "tipo_calculo": "Frecuencia",
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                },
                {
                    "variable": "SEGMENTO",
                    "pregunta_id": "SEGMENTO",
                    "texto_pregunta": "Segmento",
                    "tipo_pregunta": "RU",
                    "clasificacion_analitica": "Banner",
                    "tipo_calculo": "Frecuencia",
                    "usar_en_dashboard": True,
                    "es_banner": True,
                    "es_filtro": False,
                    "es_ponderador": False,
                },
                {
                    "variable": "POND",
                    "pregunta_id": "POND",
                    "texto_pregunta": "Ponderador",
                    "tipo_pregunta": "Ponderador",
                    "clasificacion_analitica": "Ponderador",
                    "tipo_calculo": "Frecuencia",
                    "usar_en_dashboard": False,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": True,
                },
            ]
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "parity.db"
            build_analytic_database(
                df_spss,
                Metadata(),
                datamap,
                {},
                db_path=db_path,
                export_revision=False,
            )
            options = {
                "banner": "SEGMENTO",
                "ponderador": "POND",
                "calculations": ["n", "%", "n ponderado", "% ponderado"],
                "include_significance": True,
                "confidence": 0.95,
                "min_base": 1,
            }
            direct_legacy = legacy_generate_report(db_path, "Q1", **options)
            runner_legacy = core_generate_report(
                db_path,
                "Q1",
                mode=ExecutionMode.LEGACY,
                **options,
            )
            wrapper = core_generate_report(
                db_path,
                "Q1",
                mode=ExecutionMode.CORE_WRAPPER,
                **options,
            )

        assert_report_parity(self, direct_legacy, runner_legacy)
        assert_report_parity(self, direct_legacy, wrapper)


if __name__ == "__main__":
    unittest.main()
