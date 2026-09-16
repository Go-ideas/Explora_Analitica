from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from src.database.dashboard_config import (
    apply_dashboard_configuration,
    update_datamap_configuration,
)
from src.database.db_reader import read_table
from src.database.db_writer import write_tables


class DashboardConfigurationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.df_spss = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "segmento": [1, 2, 1],
                "resultado": [5, 4, 3],
            }
        )
        self.meta = SimpleNamespace(
            column_names_to_labels={
                "id": "Identificador",
                "segmento": "Segmento",
                "resultado": "Resultado",
            }
        )
        self.datamap = pd.DataFrame(
            [
                {
                    "variable": variable,
                    "label": label,
                    "pregunta_id": variable,
                    "tipo_pregunta": "Única",
                    "clasificacion_analitica": classification,
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "tipo_calculo": "Frecuencia",
                }
                for variable, label, classification in [
                    ("id", "Identificador", "Variable técnica"),
                    (
                        "segmento",
                        "Segmento",
                        "Pregunta analizable",
                    ),
                    (
                        "resultado",
                        "Resultado",
                        "Pregunta analizable",
                    ),
                ]
            ]
        )

    def test_updates_sqlite_and_respondent_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "analytic.db"
            write_tables(
                db_path,
                {
                    "respondentes": pd.DataFrame(
                        {"id_respondente": ["1", "2", "3"]}
                    ),
                    "variables": pd.DataFrame(
                        {"variable": ["id", "segmento", "resultado"]}
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
                        {"valor": [10]}
                    ),
                },
            )

            result = apply_dashboard_configuration(
                db_path=db_path,
                df_spss=self.df_spss,
                meta_spss=self.meta,
                datamap_df=self.datamap,
                banner_variables=["segmento"],
                filter_variables=["resultado"],
            )

            config = read_table(
                db_path, "configuracion_dashboard"
            )
            respondents = read_table(db_path, "respondentes")
            variables = read_table(db_path, "variables").set_index(
                "variable"
            )
            preserved = read_table(
                db_path, "tabla_conservada"
            )

            self.assertIn("segmento", respondents.columns)
            self.assertIn("resultado", respondents.columns)
            self.assertEqual(
                set(
                    config.loc[
                        config["tipo_configuracion"].eq("banner"),
                        "variable",
                    ]
                ),
                {"segmento"},
            )
            self.assertEqual(
                set(
                    config.loc[
                        config["tipo_configuracion"].eq("filtro"),
                        "variable",
                    ]
                ),
                {"resultado"},
            )
            self.assertEqual(
                int(variables.at["segmento", "es_banner"]), 1
            )
            self.assertEqual(
                int(variables.at["resultado", "es_filtro"]), 1
            )
            self.assertEqual(preserved["valor"].tolist(), [10])
            self.assertTrue(
                bool(
                    result["datamap"]
                    .set_index("variable")
                    .at["segmento", "es_banner"]
                )
            )

    def test_rejects_unknown_variables(self) -> None:
        with self.assertRaisesRegex(
            ValueError, "no encontradas"
        ):
            update_datamap_configuration(
                self.datamap,
                banner_variables=["inexistente"],
                filter_variables=[],
            )


if __name__ == "__main__":
    unittest.main()
