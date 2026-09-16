from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest

import pandas as pd

from src.builder.analytic_db_builder import (
    build_analytic_database,
    build_configuracion_dashboard,
)
from src.builder.preguntas_builder import build_preguntas
from src.builder.recommendations_builder import (
    RECOMMENDATION_COLUMNS,
    build_recomendaciones_reporteador,
)
from src.builder.variables_builder import build_variables
from src.database.db_reader import read_table


class CommercialPersistenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.datamap = pd.DataFrame(
            [
                {
                    "variable": "A7",
                    "label": "Edad",
                    "pregunta_id": "A7",
                    "numero_pregunta": "A7",
                    "texto_pregunta": "¿Cuál es su edad?",
                    "seccion": "Perfil",
                    "seccion_cuestionario": "Perfil",
                    "bloque_cuestionario": "Demográficos",
                    "orden_cuestionario": 7,
                    "grupo_menu_reporteador": "Perfil",
                    "mostrar_en_menu_reporteador": "Sí",
                    "prioridad_reporteador": "Alta",
                    "tipo_pregunta": "RU",
                    "tipo_calculo": "Frecuencia",
                    "base_valida": "Todos",
                    "regla_transformacion": "",
                    "clasificacion_analitica": "Pregunta analizable",
                    "usar_en_dashboard": True,
                    "es_banner": True,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "es_banner_recomendado": True,
                    "es_filtro_recomendado": False,
                    "nivel_relevancia_comercial": "Alta",
                    "justificacion_banner_filtro": (
                        "Segmenta perfiles."
                    ),
                    "uso_comercial_sugerido": (
                        "Comparar resultados por edad."
                    ),
                    "riesgo_uso_analitico": (
                        "Revisar bases pequeñas."
                    ),
                    "requiere_factor": True,
                    "tipo_factor_recomendado": "Rangos de edad",
                    "variables_para_factor": "A7",
                    "regla_factor_sugerida": "18-49, 50+",
                    "justificacion_factor": "Lectura ejecutiva.",
                    "prioridad_factor": "Media",
                }
            ]
        )

    def test_questions_preserve_reporter_order_and_group(
        self,
    ) -> None:
        questions = build_preguntas(self.datamap)
        self.assertEqual(questions.iloc[0]["orden_cuestionario"], 7)
        self.assertEqual(
            questions.iloc[0]["grupo_menu_reporteador"], "Perfil"
        )

    def test_variables_preserve_commercial_explanations(
        self,
    ) -> None:
        variables = build_variables(
            pd.DataFrame({"A7": [20, 52]}),
            SimpleNamespace(column_names_to_labels={"A7": "Edad"}),
            self.datamap,
        )
        self.assertEqual(
            variables.iloc[0]["justificacion_banner_filtro"],
            "Segmenta perfiles.",
        )
        self.assertEqual(
            variables.iloc[0]["uso_comercial_sugerido"],
            "Comparar resultados por edad.",
        )

    def test_dashboard_configuration_preserves_recommendation(
        self,
    ) -> None:
        recommendations = build_recomendaciones_reporteador(
            self.datamap,
            {
                "11_Banners_Filtros_Recomendados": pd.DataFrame(
                    [
                        {
                            "Variable": "A7",
                            "Es_Banner_Recomendado": "Sí",
                            "Justificacion": "Segmenta perfiles.",
                        }
                    ]
                )
            },
        )
        configuration = build_configuracion_dashboard(
            self.datamap, recommendations
        )
        banner = configuration[
            configuration["tipo_configuracion"].eq("banner")
        ].iloc[0]
        self.assertEqual(int(banner["es_recomendado"]), 1)
        self.assertEqual(
            int(banner["es_banner_recomendado"]), 1
        )
        self.assertEqual(
            int(banner["es_filtro_recomendado"]), 0
        )
        self.assertEqual(
            banner["justificacion"], "Segmenta perfiles."
        )
        self.assertEqual(
            banner["justificacion_banner_filtro"],
            "Segmenta perfiles.",
        )

    def test_dashboard_configuration_skips_unsafe_variables(
        self,
    ) -> None:
        datamap = pd.DataFrame(
            [
                {
                    "variable": "ParentID",
                    "pregunta_id": "ID",
                    "label": "ID técnico",
                    "clasificacion_analitica": "Banner",
                    "es_banner": True,
                    "es_filtro": True,
                },
                {
                    "variable": "SEGMENTO",
                    "pregunta_id": "SEG",
                    "label": "Segmento",
                    "clasificacion_analitica": "Banner",
                    "es_banner": True,
                    "es_filtro": False,
                },
            ]
        )
        df_spss = pd.DataFrame(
            {
                "ParentID": [float("nan"), float("nan"), float("nan")],
                "SEGMENTO": ["A", "B", "A"],
            }
        )

        configuration = build_configuracion_dashboard(
            datamap, df_spss=df_spss
        )

        self.assertNotIn(
            "ParentID", configuration["variable"].tolist()
        )
        self.assertIn(
            "SEGMENTO", configuration["variable"].tolist()
        )

    def test_reporter_recommendations_use_all_three_sheets(
        self,
    ) -> None:
        sheets = {
            "11_Banners_Filtros_Recomendados": pd.DataFrame(
                [
                    {
                        "Variable": "A7",
                        "Variable_Label": "Edad",
                        "Es_Banner_Recomendado": "Sí",
                    }
                ]
            ),
            "12_Factores_Scores_Recomendados": pd.DataFrame(
                [
                    {
                        "Numero_Pregunta": "A7",
                        "Variables_Para_Factor": "A7",
                        "Requiere_Factor": "Sí",
                        "Tipo_Factor_Recomendado": "Rangos de edad",
                    }
                ]
            ),
            "13_Orden_Menu_Reporteador": pd.DataFrame(
                [
                    {
                        "Numero_Pregunta": "A7",
                        "Variables_SPSS_Asociadas": "A7",
                        "Seccion_Cuestionario": "Perfil",
                    }
                ]
            ),
        }
        recommendations = build_recomendaciones_reporteador(
            self.datamap, sheets
        )
        self.assertEqual(
            list(recommendations.columns), RECOMMENDATION_COLUMNS
        )
        self.assertEqual(
            set(recommendations["tipo_recomendacion"]),
            {"banner_filtro", "factor_score", "orden_menu"},
        )
        self.assertEqual(
            set(recommendations["fuente_hoja"]),
            set(sheets),
        )

    def test_database_contains_reporter_recommendations_table(
        self,
    ) -> None:
        meta = SimpleNamespace(
            column_names_to_labels={"A7": "Edad"},
            variable_value_labels={},
            missing_ranges={},
            missing_user_values={},
        )
        sheets = {
            "11_Banners_Filtros_Recomendados": pd.DataFrame(
                [
                    {
                        "Variable": "A7",
                        "Es_Banner_Recomendado": "Sí",
                        "Justificacion": "Segmenta perfiles.",
                    }
                ]
            )
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "analytic.db"
            build_analytic_database(
                pd.DataFrame({"A7": [20, 52]}),
                meta,
                self.datamap,
                sheets,
                db_path,
                root / "revision.xlsx",
            )
            stored = read_table(
                db_path, "recomendaciones_reporteador"
            )
            stored_questions = read_table(db_path, "preguntas")
            stored_variables = read_table(db_path, "variables")

        self.assertFalse(stored.empty)
        self.assertEqual(
            stored.iloc[0]["fuente_hoja"],
            "11_Banners_Filtros_Recomendados",
        )
        self.assertIn(
            "grupo_menu_reporteador", stored_questions.columns
        )
        self.assertIn(
            "uso_comercial_sugerido", stored_variables.columns
        )

    def test_fast_build_can_skip_revision_excel(
        self,
    ) -> None:
        meta = SimpleNamespace(
            column_names_to_labels={"A7": "Edad"},
            variable_value_labels={},
            missing_ranges={},
            missing_user_values={},
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "analytic.db"
            excel_path = root / "revision.xlsx"
            result = build_analytic_database(
                pd.DataFrame({"A7": [20, 52]}),
                meta,
                self.datamap,
                {},
                db_path,
                excel_path,
                export_revision=False,
            )

            self.assertTrue(db_path.exists())
            self.assertFalse(excel_path.exists())
            self.assertIsNone(result["excel_path"])

    def test_build_does_not_inherit_active_factors_from_previous_database(
        self,
    ) -> None:
        meta = SimpleNamespace(
            column_names_to_labels={"F3r": "Rango de edad"},
            variable_value_labels={},
            missing_ranges={},
            missing_user_values={},
        )
        datamap = self.datamap.copy()
        datamap["variable"] = "F3r"
        datamap["label"] = "Rango de edad"
        datamap["pregunta_id"] = "F3"
        datamap["numero_pregunta"] = "F3"
        datamap["texto_pregunta"] = "¿Cuántos años tiene?"
        datamap["variables_para_factor"] = "F3r"

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            db_path = root / "analytic.db"
            conn = sqlite3.connect(db_path)
            try:
                conn.execute(
                    """
                    CREATE TABLE factores_configurados (
                        factor_id TEXT,
                        numero_pregunta TEXT,
                        texto_pregunta TEXT,
                        activo INTEGER,
                        tipo_factor TEXT,
                        variables_fuente TEXT,
                        regla_factor TEXT,
                        justificacion_factor TEXT,
                        uso_comercial TEXT,
                        prioridad_factor TEXT,
                        configuracion_json TEXT,
                        variable_derivada TEXT,
                        como_banner INTEGER,
                        como_filtro INTEGER,
                        actualizado_en TEXT
                    )
                    """
                )
                conn.execute(
                    """
                    INSERT INTO factores_configurados VALUES (
                        'A7::Rangos de edad::0',
                        'A7',
                        '¿Cuál es su edad?',
                        1,
                        'Rangos de edad',
                        'A7',
                        '18-49, 50+',
                        'Viejo factor',
                        'Vieja segmentación',
                        'Media',
                        '{"ranges": []}',
                        'FACTOR_A7',
                        1,
                        1,
                        '2026-07-02T15:57:17-06:00'
                    )
                    """
                )
                conn.commit()
            finally:
                conn.close()

            build_analytic_database(
                pd.DataFrame({"F3r": [1, 2, 3]}),
                meta,
                datamap,
                {},
                db_path,
                root / "revision.xlsx",
            )
            factors = read_table(db_path, "factores_configurados")
            variables = read_table(db_path, "variables")

        self.assertTrue(factors.empty)
        self.assertNotIn(
            "FACTOR_A7",
            variables["variable"].astype(str).tolist(),
        )

    def test_recommendations_fall_back_to_normalized_datamap(
        self,
    ) -> None:
        recommendations = build_recomendaciones_reporteador(
            self.datamap, {}
        )
        self.assertEqual(
            set(recommendations["tipo_recomendacion"]),
            {"banner_filtro", "factor_score", "orden_menu"},
        )
        self.assertEqual(
            set(recommendations["fuente_hoja"]),
            {
                "08_Clasificacion_Analitica",
                "10_Datamap_Corregido",
            },
        )


if __name__ == "__main__":
    unittest.main()
