from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.builder.analytic_db_builder import build_analytic_database
from src.builder.respuestas_long_builder import (
    build_respuestas_long,
)
from src.database.db_reader import read_table
from src.export.datamap_exporter import save_final_datamap
from src.readers.datamap_reader import (
    get_review_source_sheet,
    normalize_review_datamap,
)
from src.reporter.tabulator import available_questions, generate_report
from src.reporter.filters import config_entries


class DatamapCompatibilityTests(unittest.TestCase):
    def test_merges_question_metadata_into_variable_roles(self) -> None:
        sheets = {
            "08_Clasificacion_Analitica": pd.DataFrame(
                [
                    {
                        "Variable": "RM_1",
                        "Variable_Label": "Primera mención",
                        "Rol_Analitico_Principal": (
                            "Pregunta analizable"
                        ),
                        "Usar_En_Dashboard": "Sí",
                        "Es_Banner": "No",
                        "Es_Filtro": "No",
                    },
                    {
                        "Variable": "RM_2",
                        "Variable_Label": "Segunda mención",
                        "Rol_Analitico_Principal": (
                            "Pregunta analizable"
                        ),
                        "Usar_En_Dashboard": "Sí",
                        "Es_Banner": "No",
                        "Es_Filtro": "No",
                    },
                    {
                        "Variable": "COD_1",
                        "Variable_Label": "Código abierto",
                        "Rol_Analitico_Principal": (
                            "Abierta codificada"
                        ),
                        "Usar_En_Dashboard": "Sí",
                        "Es_Banner": "No",
                        "Es_Filtro": "No",
                    },
                ]
            ),
            "10_Datamap_Corregido": pd.DataFrame(
                [
                    {
                        "Orden_Cuestionario": 1,
                        "Seccion_Cuestionario": "Sección A",
                        "Numero_Pregunta": "Q1",
                        "Texto_Pregunta": "Pregunta múltiple",
                        "Tipo_Pregunta_Cuestionario": "RM",
                        "Variables_SPSS_Asociadas": "RM_1, RM_2",
                    },
                    {
                        "Orden_Cuestionario": 2,
                        "Seccion_Cuestionario": "Sección B",
                        "Numero_Pregunta": "Q2",
                        "Texto_Pregunta": "Abierta codificada",
                        "Tipo_Pregunta_Cuestionario": (
                            "Abierta / codificada"
                        ),
                        "Variables_SPSS_Asociadas": "COD_1",
                    },
                ]
            ),
        }

        _, source = get_review_source_sheet(sheets)
        review = normalize_review_datamap(
            source, ["RM_1", "RM_2", "COD_1"]
        ).set_index("variable")

        self.assertEqual(review.at["RM_1", "pregunta_id"], "Q1")
        self.assertEqual(review.at["RM_2", "tipo_pregunta"], "RM")
        self.assertEqual(
            review.at["RM_1", "tipo_calculo"],
            "RM % Respondentes",
        )
        self.assertEqual(
            review.at["COD_1", "clasificacion_analitica"],
            "Pregunta analizable",
        )
        self.assertEqual(
            review.at["COD_1", "tipo_pregunta"],
            "RM codificada",
        )

    def test_atlas_aliases_recommendations_grids_and_weights(self) -> None:
        sheets = {
            "10_Datamap_Corregido": pd.DataFrame(
                [
                    {
                        "Numero_Pregunta": "C7",
                        "Texto_Pregunta": "Evaluación de atributos",
                        "Tipo_Final_QA": "Grid",
                        "Variables_Finales": "C7_1, C7_2",
                        "Usar_En_Reporteador": "Sí",
                    }
                ]
            ),
            "08_Clasificacion_Analitica": pd.DataFrame(
                [
                    {
                        "Variable": "C7_1",
                        "Variable_Label": "Sabor",
                        "Rol_Analitico": "Pregunta analizable",
                    },
                    {
                        "Variable": "C7_2",
                        "Variable_Label": "Precio",
                        "Rol_Analitico": "Pregunta analizable",
                    },
                ]
            ),
            "11_Banners_Filtros_Recomendados": pd.DataFrame(
                [
                    {
                        "Variable": "SEGMENTO",
                        "Es_Banner_Recomendado": "Sí",
                        "Justificacion_Banner_Filtro": (
                            "Segmenta lectura comercial."
                        ),
                    }
                ]
            ),
            "04B_Check_Grids": pd.DataFrame(
                [
                    {
                        "Pregunta_Padre": "C7",
                        "Grid_ID": "C7",
                        "Variable_Item": "C7_1",
                        "Es_Item_Grid": "Sí",
                        "Texto_Fila_Grid": "Sabor",
                        "Metrica_Grid_Recomendada": "Media",
                    }
                ]
            ),
        }

        source_name, source = get_review_source_sheet(sheets)
        review = normalize_review_datamap(
            source,
            ["C7_1", "C7_2", "SEGMENTO", "Pond_Total"],
        ).set_index("variable")

        self.assertEqual(source_name, "10_Datamap_Corregido")
        self.assertEqual(review.at["C7_1", "pregunta_id"], "C7")
        self.assertTrue(review.at["C7_1", "es_item_grid"])
        self.assertEqual(
            review.at["C7_1", "metrica_grid_recomendada"],
            "Media",
        )
        self.assertTrue(review.at["SEGMENTO", "es_banner"])
        self.assertEqual(
            review.at["SEGMENTO", "justificacion_banner_filtro"],
            "Segmenta lectura comercial.",
        )
        self.assertEqual(
            review.at["Pond_Total", "clasificacion_analitica"],
            "Ponderador",
        )
        self.assertTrue(review.at["Pond_Total", "es_ponderador"])
        self.assertFalse(review.at["Pond_Total", "usar_en_dashboard"])

    def test_final_datamap_preserves_question_sheets(self) -> None:
        question_sheet = pd.DataFrame(
            {
                "Numero_Pregunta": ["Q1"],
                "Variables_SPSS_Asociadas": ["V1"],
            }
        )
        recommendation_sheet = pd.DataFrame(
            {
                "Variable": ["V1"],
                "Es_Banner_Recomendado": ["Sí"],
            }
        )
        sheets = {
            "08_Clasificacion_Analitica": pd.DataFrame(
                {"Variable": ["V1"]}
            ),
            "10_Datamap_Corregido": question_sheet,
            "11_Banners_Filtros_Recomendados": (
                recommendation_sheet
            ),
        }
        review = pd.DataFrame(
            {
                "variable": ["V1"],
                "pregunta_id": ["Q1"],
            }
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Datamap_Final.xlsx"
            save_final_datamap(path, sheets, review)
            saved = pd.read_excel(path, sheet_name=None)

        pd.testing.assert_frame_equal(
            saved["10_Datamap_Corregido"],
            question_sheet,
        )
        saved_recommendations = saved[
            "11_Banners_Filtros_Recomendados"
        ]
        self.assertEqual(
            saved_recommendations["Variable"].tolist(), ["V1"]
        )
        self.assertEqual(
            saved_recommendations[
                "Es_Banner_Recomendado"
            ].tolist(),
            ["Sí"],
        )
        self.assertIn(
            "Justificacion_Banner_Filtro",
            saved_recommendations.columns,
        )
        self.assertIn(
            "Distribucion_Base",
            saved_recommendations.columns,
        )
        self.assertEqual(
            saved["08_Clasificacion_Analitica"].columns.tolist(),
            ["Variable", "Pregunta_ID"],
        )

    def test_banner_can_also_be_a_reportable_question(self) -> None:
        df_spss = pd.DataFrame({"CIUDAD": [1.0, 2.0]})
        datamap = pd.DataFrame(
            [
                {
                    "variable": "CIUDAD",
                    "pregunta_id": "Q_CIUDAD",
                    "tipo_pregunta": "RU / banner",
                    "tipo_calculo": "Frecuencia",
                    "clasificacion_analitica": "Banner",
                    "usar_en_dashboard": True,
                    "es_ponderador": False,
                }
            ]
        )
        respondents = pd.DataFrame(
            {"id_respondente": ["1", "2"]}
        )

        class Metadata:
            variable_value_labels = {
                "CIUDAD": {1.0: "Norte", 2.0: "Sur"}
            }

        result = build_respuestas_long(
            df_spss, Metadata(), datamap, respondents
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(
            result["pregunta_id"].unique().tolist(),
            ["Q_CIUDAD"],
        )

    def test_grid_rm_builds_grouped_report(self) -> None:
        df_spss = pd.DataFrame(
            {
                "BRAND_A_REASON_1": [1, 0, 1, 0],
                "BRAND_A_REASON_2": [0, 1, 1, 0],
                "BRAND_B_REASON_1": [1, 0, 0, 0],
                "SEGMENTO": [1, 1, 2, 2],
            }
        )
        datamap = pd.DataFrame(
            [
                {
                    "variable": "BRAND_A_REASON_1",
                    "label": "Brand A - Precio",
                    "pregunta_id": "HC9",
                    "numero_pregunta": "HC9",
                    "texto_pregunta": "Razones por marca",
                    "tipo_pregunta": "GRID_RM/LOOP_RM",
                    "clasificacion_analitica": "Pregunta analizable",
                    "tipo_calculo": "Multirrespuesta agrupada",
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "grid_id": "HC9",
                    "pregunta_padre": "HC9",
                    "tipo_estructura_grid": "GRID_RM",
                    "es_grid": True,
                    "es_item_grid": True,
                    "es_grid_rm_loop": True,
                    "entidad_loop": "Brand A",
                    "codigo_opcion_rm": "1",
                    "label_opcion_rm": "Precio",
                },
                {
                    "variable": "BRAND_A_REASON_2",
                    "label": "Brand A - Calidad",
                    "pregunta_id": "HC9",
                    "numero_pregunta": "HC9",
                    "texto_pregunta": "Razones por marca",
                    "tipo_pregunta": "GRID_RM/LOOP_RM",
                    "clasificacion_analitica": "Pregunta analizable",
                    "tipo_calculo": "Multirrespuesta agrupada",
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "grid_id": "HC9",
                    "pregunta_padre": "HC9",
                    "tipo_estructura_grid": "GRID_RM",
                    "es_grid": True,
                    "es_item_grid": True,
                    "es_grid_rm_loop": True,
                    "entidad_loop": "Brand A",
                    "codigo_opcion_rm": "2",
                    "label_opcion_rm": "Calidad",
                },
                {
                    "variable": "BRAND_B_REASON_1",
                    "label": "Brand B - Precio",
                    "pregunta_id": "HC9",
                    "numero_pregunta": "HC9",
                    "texto_pregunta": "Razones por marca",
                    "tipo_pregunta": "GRID_RM/LOOP_RM",
                    "clasificacion_analitica": "Pregunta analizable",
                    "tipo_calculo": "Multirrespuesta agrupada",
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "grid_id": "HC9",
                    "pregunta_padre": "HC9",
                    "tipo_estructura_grid": "GRID_RM",
                    "es_grid": True,
                    "es_item_grid": True,
                    "es_grid_rm_loop": True,
                    "entidad_loop": "Brand B",
                    "codigo_opcion_rm": "1",
                    "label_opcion_rm": "Precio",
                },
                {
                    "variable": "SEGMENTO",
                    "label": "Segmento",
                    "pregunta_id": "SEGMENTO",
                    "numero_pregunta": "SEGMENTO",
                    "texto_pregunta": "Segmento",
                    "tipo_pregunta": "RU",
                    "clasificacion_analitica": "Banner",
                    "tipo_calculo": "Frecuencia",
                    "usar_en_dashboard": True,
                    "es_banner": True,
                    "es_filtro": False,
                    "es_ponderador": False,
                },
            ]
        )

        class Metadata:
            variable_value_labels = {}
            variable_labels = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "grid_rm.db"
            build_analytic_database(
                df_spss,
                Metadata(),
                datamap,
                {},
                db_path=db_path,
                export_revision=False,
            )
            questions = available_questions(db_path)
            report = generate_report(
                db_path,
                "HC9",
                calculations=["% respondentes", "Menciones"],
            )
            grid_loop = read_table(db_path, "respuestas_grid_loop")
            banners = config_entries(db_path, "banner")

        selected = questions[
            questions["pregunta_id"].astype(str).eq("HC9")
        ].iloc[0]
        self.assertEqual(
            selected["tipo_pregunta_reporter"], "GRID_RM/LOOP_RM"
        )
        self.assertEqual(report.question_type, "GRID_RM/LOOP_RM")
        self.assertIn("Entidad", report.table.columns)
        self.assertIn("Opción", report.table.columns)
        self.assertIn("Total | % respondentes", report.table.columns)
        self.assertIn("Total | Menciones", report.table.columns)
        brand_a_price = report.table[
            (report.table["Entidad"] == "Brand A")
            & (report.table["Opción"] == "Precio")
        ].iloc[0]
        self.assertEqual(brand_a_price["Total | Menciones"], 2)
        self.assertAlmostEqual(
            brand_a_price["Total | % respondentes"], 50.0
        )
        self.assertEqual(len(grid_loop), 12)
        self.assertEqual(int(grid_loop["base_valida"].sum()), 12)
        self.assertIn("SEGMENTO", banners["variable"].tolist())
        self.assertNotIn(
            "BRAND_A_REASON_1", banners["variable"].tolist()
        )
        self.assertFalse(
            any(metric in report.calculations for metric in ["Media", "Top2Box", "NPS"])
        )


if __name__ == "__main__":
    unittest.main()
