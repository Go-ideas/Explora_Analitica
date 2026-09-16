from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.database.db_reader import read_table
from src.database.db_writer import write_tables
from src.database.factor_processor import (
    apply_range_factor,
    synchronize_inactive_factors,
)
from src.reporter.factors import (
    apply_numeric_ranges,
    parse_recommended_ranges,
    recommended_factor_calculations,
    validate_ranges,
)
from src.reporter.tabulator import available_questions
from src.reporter.recommendations import (
    load_factor_configurations,
    save_factor_configurations,
)


class FactorProcessingTests(unittest.TestCase):
    def test_factor_recommendations_define_default_calculations(
        self,
    ) -> None:
        scale = pd.DataFrame(
            [
                {
                    "Tipo_Factor_Recomendado": (
                        "Top2Box claridad"
                    ),
                    "Regla_Factor_Sugerida": (
                        "Top2Box=4-5; Bottom2Box=1-2; "
                        "media de escala"
                    ),
                }
            ]
        )
        rm = pd.DataFrame(
            [
                {
                    "Tipo_Factor_Recomendado": (
                        "Índice de barreras"
                    ),
                    "Regla_Factor_Sugerida": (
                        "Reportar % de menciones para RM"
                    ),
                }
            ]
        )
        nps = pd.DataFrame(
            [
                {
                    "Tipo_Factor_Recomendado": "NPS",
                    "Regla_Factor_Sugerida": (
                        "NPS=%Promotores-%Detractores"
                    ),
                }
            ]
        )

        self.assertEqual(
            recommended_factor_calculations(
                "Escala", ["Media"], scale
            ),
            ["Media", "Top2Box", "BottomBox"],
        )
        self.assertEqual(
            recommended_factor_calculations(
                "RM", ["n"], rm
            ),
            [
                "n",
                "RM % Respondentes",
                "RM % Menciones",
            ],
        )
        self.assertEqual(
            recommended_factor_calculations(
                "NPS", ["NPS"], nps
            ),
            ["NPS"],
        )

    def test_parses_and_applies_recommended_age_ranges(self) -> None:
        ranges = parse_recommended_ranges(
            "Sugerir rangos: 18-49, 50-59, 60-69, 70+"
        )
        self.assertEqual(
            [row["Etiqueta"] for row in ranges],
            ["18-49", "50-59", "60-69", "70+"],
        )
        derived = apply_numeric_ranges(
            pd.Series([18, 49, 50, 69, 70, None]),
            ranges,
        )
        self.assertEqual(
            derived.fillna("missing").tolist(),
            [
                "18-49",
                "18-49",
                "50-59",
                "60-69",
                "70+",
                "missing",
            ],
        )

    def test_rejects_overlapping_ranges(self) -> None:
        with self.assertRaisesRegex(ValueError, "traslapan"):
            validate_ranges(
                [
                    {
                        "Incluir": True,
                        "Etiqueta": "A",
                        "Mínimo": 1,
                        "Máximo": 10,
                    },
                    {
                        "Incluir": True,
                        "Etiqueta": "B",
                        "Mínimo": 10,
                        "Máximo": 20,
                    },
                ]
            )

    def test_persists_and_processes_range_factor(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "analytic.db"
            variables = pd.DataFrame(
                [
                    {
                        "variable": "EDAD",
                        "label": "Edad",
                        "tipo_spss": "numeric",
                        "pregunta_id": "Q_EDAD",
                        "tipo_pregunta": "RU",
                        "clasificacion_analitica": (
                            "Pregunta analizable"
                        ),
                        "usar_en_dashboard": 1,
                        "es_banner": 0,
                        "es_filtro": 0,
                        "es_ponderador": 0,
                        "tipo_calculo": "Frecuencia",
                        "n_validos": 4,
                        "n_missing": 0,
                        "valores_unicos": 4,
                        "min": 20,
                        "max": 72,
                    }
                ]
            )
            write_tables(
                db_path,
                {
                    "respondentes": pd.DataFrame(
                        {
                            "id_respondente": ["1", "2", "3", "4"],
                            "id_original": ["1", "2", "3", "4"],
                            "row_index": [0, 1, 2, 3],
                        }
                    ),
                    "variables": variables,
                    "opciones": pd.DataFrame(
                        columns=[
                            "variable",
                            "pregunta_id",
                            "codigo",
                            "label",
                            "es_otro",
                            "es_exclusiva",
                            "orden",
                        ]
                    ),
                    "configuracion_dashboard": pd.DataFrame(
                        columns=[
                            "tipo_configuracion",
                            "variable",
                            "pregunta_id",
                            "label",
                        ]
                    ),
                    "tabla_conservada": pd.DataFrame(
                        {"valor": [1]}
                    ),
                },
            )
            factor_id = "Q_EDAD::Rangos::0"
            factors = pd.DataFrame(
                [
                    {
                        "_factor_id": factor_id,
                        "Activo": True,
                        "Numero_Pregunta": "Q_EDAD",
                        "Texto_Pregunta": "Edad",
                        "Tipo_Factor_Recomendado": "Rangos",
                        "Variables_Para_Factor": "EDAD",
                        "Regla_Factor_Sugerida": "18-49, 50+",
                        "Justificacion_Factor": "Lectura ejecutiva",
                        "Uso_Comercial_Sugerido": "Segmentación",
                        "Prioridad_Factor": "Alta",
                    }
                ]
            )
            ranges = parse_recommended_ranges("18-49, 50+")
            save_factor_configurations(
                db_path, factors, {factor_id: ranges}
            )

            result = apply_range_factor(
                db_path=db_path,
                source_values=pd.Series([20, 49, 50, 72]),
                source_variable="EDAD",
                factor_variable="FACTOR_EDAD",
                factor_label="Rangos de edad",
                factor_id=factor_id,
                ranges=ranges,
                as_banner=True,
                as_filter=False,
            )

            respondents = read_table(db_path, "respondentes")
            config = read_table(
                db_path, "configuracion_dashboard"
            )
            built_variables = read_table(
                db_path, "variables"
            ).set_index("variable")
            built_questions = read_table(
                db_path, "preguntas"
            )
            built_responses = read_table(
                db_path, "respuestas_long"
            )
            built_options = read_table(db_path, "opciones")
            question_catalog = available_questions(db_path)
            saved = load_factor_configurations(db_path)
            preserved = read_table(
                db_path, "tabla_conservada"
            )

        self.assertEqual(
            respondents["FACTOR_EDAD"].tolist(),
            ["18-49", "18-49", "50+", "50+"],
        )
        self.assertEqual(
            set(
                config.loc[
                    config["variable"].eq("FACTOR_EDAD"),
                    "tipo_configuracion",
                ]
            ),
            {"banner"},
        )
        self.assertEqual(
            saved.iloc[0]["variable_derivada"], "FACTOR_EDAD"
        )
        self.assertEqual(int(saved.iloc[0]["activo"]), 1)
        self.assertEqual(int(saved.iloc[0]["como_banner"]), 1)
        self.assertEqual(int(saved.iloc[0]["como_filtro"]), 0)
        self.assertEqual(
            int(built_variables.at["FACTOR_EDAD", "es_banner"]), 1
        )
        self.assertEqual(
            int(built_variables.at["FACTOR_EDAD", "es_filtro"]), 0
        )
        self.assertIn(
            "FACTOR_EDAD",
            built_questions["pregunta_id"].astype(str).tolist(),
        )
        self.assertEqual(
            set(
                built_responses.loc[
                    built_responses["pregunta_id"].eq(
                        "FACTOR_EDAD"
                    ),
                    "respuesta_label",
                ]
            ),
            {"18-49", "50+"},
        )
        self.assertTrue(
            built_options["pregunta_id"]
            .astype(str)
            .eq("FACTOR_EDAD")
            .all()
        )
        self.assertIn(
            "FACTOR_EDAD",
            question_catalog["pregunta_id"].astype(str).tolist(),
        )
        self.assertEqual(preserved["valor"].tolist(), [1])
        self.assertEqual(result["validos"], 4)

    def test_inactive_factor_is_not_exposed_as_active_variable(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "analytic.db"
            write_tables(
                db_path,
                {
                    "respondentes": pd.DataFrame(
                        {
                            "id_respondente": ["1"],
                            "row_index": [0],
                            "FACTOR_EDAD": ["18-49"],
                        }
                    ),
                    "variables": pd.DataFrame(
                        [
                            {
                                "variable": "FACTOR_EDAD",
                                "clasificacion_analitica": "Derivada",
                                "es_banner": 1,
                                "es_filtro": 1,
                            }
                        ]
                    ),
                    "opciones": pd.DataFrame(
                        [{"variable": "FACTOR_EDAD", "codigo": "18-49"}]
                    ),
                    "configuracion_dashboard": pd.DataFrame(
                        [
                            {
                                "tipo_configuracion": "banner",
                                "variable": "FACTOR_EDAD",
                            },
                            {
                                "tipo_configuracion": "filtro",
                                "variable": "FACTOR_EDAD",
                            },
                        ]
                    ),
                    "preguntas": pd.DataFrame(
                        [
                            {
                                "pregunta_id": "FACTOR_EDAD",
                                "texto_pregunta": "Rangos de edad",
                                "usar_en_dashboard": 1,
                            }
                        ]
                    ),
                    "respuestas_long": pd.DataFrame(
                        [
                            {
                                "id_respondente": "1",
                                "pregunta_id": "FACTOR_EDAD",
                                "variable": "FACTOR_EDAD",
                                "respuesta_label": "18-49",
                            }
                        ]
                    ),
                    "factores_configurados": pd.DataFrame(
                        [
                            {
                                "factor_id": "Q_EDAD::Rangos::0",
                                "activo": 0,
                                "variable_derivada": "FACTOR_EDAD",
                            }
                        ]
                    ),
                },
            )

            result = synchronize_inactive_factors(db_path)
            respondents = read_table(db_path, "respondentes")
            variables = read_table(db_path, "variables")
            config = read_table(
                db_path, "configuracion_dashboard"
            )
            questions = read_table(db_path, "preguntas")
            responses = read_table(
                db_path, "respuestas_long"
            )

        self.assertEqual(result["removed"], ["FACTOR_EDAD"])
        self.assertNotIn("FACTOR_EDAD", respondents.columns)
        self.assertNotIn(
            "FACTOR_EDAD",
            variables.get("variable", pd.Series(dtype=str)).tolist(),
        )
        self.assertNotIn(
            "FACTOR_EDAD",
            config.get("variable", pd.Series(dtype=str)).tolist(),
        )
        self.assertNotIn(
            "FACTOR_EDAD",
            questions.get(
                "pregunta_id", pd.Series(dtype=str)
            ).tolist(),
        )
        self.assertNotIn(
            "FACTOR_EDAD",
            responses.get(
                "pregunta_id", pd.Series(dtype=str)
            ).tolist(),
        )


if __name__ == "__main__":
    unittest.main()
