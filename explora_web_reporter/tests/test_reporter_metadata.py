from __future__ import annotations

from io import BytesIO
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.database.db_writer import write_tables
from src.export.excel_exporter import (
    export_report_table_to_excel,
)
from src.reporter.recommendations import configuration_entries
from src.utils.question_order import (
    ADDITIONAL_SECTION,
    order_question_catalog,
)


class ReporterMetadataTests(unittest.TestCase):
    def test_questionnaire_order_and_additional_section(self) -> None:
        questions = pd.DataFrame(
            [
                {
                    "pregunta_id": "Q2",
                    "texto_pregunta": "Segunda",
                    "seccion_reporter": "General",
                },
                {
                    "pregunta_id": "EXTRA",
                    "texto_pregunta": "Variable derivada",
                    "seccion_reporter": "General",
                },
                {
                    "pregunta_id": "Q1",
                    "texto_pregunta": "Primera",
                    "seccion_reporter": "General",
                },
                {
                    "pregunta_id": "FOLIO",
                    "texto_pregunta": "Folio",
                    "seccion_reporter": "General",
                    "clasificacion_analitica": "Variable técnica",
                },
            ]
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "datamap.xlsx"
            with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
                pd.DataFrame(
                    [
                        {
                            "Pregunta_ID": "Q1",
                            "Sección": "Bloque A",
                            "Texto_Pregunta": "Primera",
                        },
                        {
                            "Pregunta_ID": "Q2",
                            "Sección": "Bloque A",
                            "Texto_Pregunta": "Segunda",
                        },
                    ]
                ).to_excel(
                    writer,
                    sheet_name="10_Datamap_Corregido",
                    index=False,
                )
                pd.DataFrame(
                    [
                        {
                            "Pregunta_ID": "Q2",
                            "Orden_Cuestionario": 1,
                        },
                        {
                            "Pregunta_ID": "Q1",
                            "Orden_Cuestionario": 2,
                        },
                    ]
                ).to_excel(
                    writer,
                    sheet_name="13_Orden_Menu_Reporteador",
                    index=False,
                )

            result = order_question_catalog(questions, [path])

        self.assertEqual(
            result["pregunta_id"].tolist(),
            ["Q2", "Q1", "EXTRA"],
        )
        self.assertEqual(
            result.iloc[-1]["seccion_reporter"],
            ADDITIONAL_SECTION,
        )

    def test_recommended_entries_are_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "analytic.db"
            datamap_path = root / "datamap.xlsx"
            write_tables(
                db_path,
                {
                    "respondentes": pd.DataFrame(
                        {
                            "id_respondente": ["1"],
                            "CONFIG": [1],
                            "SUGERIDA": [2],
                        }
                    ),
                    "variables": pd.DataFrame(
                        [
                            {
                                "variable": "CONFIG",
                                "label": "Configurada",
                                "pregunta_id": "Q1",
                            },
                            {
                                "variable": "SUGERIDA",
                                "label": "Sugerida",
                                "pregunta_id": "Q2",
                            },
                        ]
                    ),
                    "configuracion_dashboard": pd.DataFrame(
                        [
                            {
                                "tipo_configuracion": "banner",
                                "variable": "CONFIG",
                                "pregunta_id": "Q1",
                                "label": "Configurada",
                            }
                        ]
                    ),
                },
            )
            with pd.ExcelWriter(
                datamap_path, engine="xlsxwriter"
            ) as writer:
                pd.DataFrame(
                    [
                        {
                            "Variable": "SUGERIDA",
                            "Es_Filtro_Recomendado": "Sí",
                            "Justificacion_Banner_Filtro": (
                                "Segmentación comercial"
                            ),
                        }
                    ]
                ).to_excel(
                    writer,
                    sheet_name="11_Banners_Filtros_Recomendados",
                    index=False,
                )

            banners = configuration_entries(
                db_path, "banner", [datamap_path]
            )
            filters = configuration_entries(
                db_path, "filtro", [datamap_path]
            )

        self.assertEqual(banners.iloc[0]["variable"], "CONFIG")
        suggested = filters.set_index("variable").loc["SUGERIDA"]
        self.assertTrue(bool(suggested["es_recomendado"]))
        self.assertEqual(
            suggested["justificacion"],
            "Segmentación comercial",
        )

    def test_current_export_contains_method_notes(self) -> None:
        output = BytesIO()
        export_report_table_to_excel(
            pd.DataFrame(
                {
                    "Respuesta": ["Sí"],
                    "Total | %": [100.0],
                }
            ),
            {"Pregunta": "Q1"},
            output,
            notes=["Nota metodológica"],
        )
        output.seek(0)
        with pd.ExcelFile(output) as workbook:
            self.assertIn(
                "Notas_Metodologicas", workbook.sheet_names
            )


if __name__ == "__main__":
    unittest.main()
