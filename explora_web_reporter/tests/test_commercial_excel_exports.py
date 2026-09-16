from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.export.datamap_exporter import save_final_datamap
from src.export.excel_exporter import export_revision_excel


class CommercialExcelExportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.review = pd.DataFrame(
            [
                {
                    "variable": "A7",
                    "label": "Edad",
                    "clasificacion_analitica": (
                        "Pregunta analizable"
                    ),
                    "usar_en_dashboard": True,
                    "es_banner": False,
                    "es_filtro": False,
                    "es_ponderador": False,
                    "orden_cuestionario": 7,
                    "seccion_cuestionario": "Perfil",
                    "bloque_cuestionario": "Demográficos",
                    "grupo_menu_reporteador": "Perfil",
                    "mostrar_en_menu_reporteador": "Sí",
                    "prioridad_reporteador": "Alta",
                    "es_banner_recomendado": True,
                    "es_filtro_recomendado": False,
                    "nivel_relevancia_comercial": "Alta",
                    "justificacion_banner_filtro": (
                        "Segmenta perfiles."
                    ),
                    "uso_comercial_sugerido": (
                        "Comparar por edad."
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
        self.sheets = {
            "08_Clasificacion_Analitica": pd.DataFrame(
                [
                    {
                        "Variable": "A7",
                        "Variable_Label": "Edad",
                        "Rol_Analitico_Principal": (
                            "Pregunta analizable"
                        ),
                        "Columna_Desconocida": "Conservar",
                    }
                ]
            ),
            "10_Datamap_Corregido": pd.DataFrame(
                [
                    {
                        "Numero_Pregunta": "A7",
                        "Orden_Cuestionario": 7,
                        "Seccion_Cuestionario": "Perfil",
                        "Uso_Comercial_Sugerido": (
                            "Comparar por edad."
                        ),
                    }
                ]
            ),
            "11_Banners_Filtros_Recomendados": pd.DataFrame(
                [{"Variable": "A7"}]
            ),
            "12_Factores_Scores_Recomendados": pd.DataFrame(
                [{"Numero_Pregunta": "A7"}]
            ),
            "13_Orden_Menu_Reporteador": pd.DataFrame(
                [{"Numero_Pregunta": "A7"}]
            ),
            "Hoja_Desconocida": pd.DataFrame(
                [{"Dato": "Conservar"}]
            ),
        }

    def test_final_datamap_preserves_sheets_and_columns(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Datamap_Final.xlsx"
            save_final_datamap(path, self.sheets, self.review)
            exported = pd.read_excel(path, sheet_name=None)

        self.assertEqual(set(exported), set(self.sheets))
        classification = exported[
            "08_Clasificacion_Analitica"
        ]
        for column in (
            "Orden_Cuestionario",
            "Seccion_Cuestionario",
            "Grupo_Menu_Reporteador",
            "Es_Banner_Recomendado",
            "Justificacion_Banner_Filtro",
            "Uso_Comercial_Sugerido",
            "Tipo_Factor_Recomendado",
        ):
            self.assertIn(column, classification.columns)
        self.assertEqual(
            classification.iloc[0]["Columna_Desconocida"],
            "Conservar",
        )
        self.assertEqual(
            exported["10_Datamap_Corregido"].columns.tolist(),
            self.sheets[
                "10_Datamap_Corregido"
            ].columns.tolist(),
        )

    def test_revision_excel_includes_source_recommendations(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "revision.xlsx"
            export_revision_excel(
                path, {}, datamap_sheets=self.sheets
            )
            with pd.ExcelFile(path) as workbook:
                sheet_names = workbook.sheet_names

        self.assertIn(
            "Banners_Filtros_Recomendados", sheet_names
        )
        self.assertIn(
            "Factores_Scores_Recomendados", sheet_names
        )
        self.assertIn("Orden_Menu_Reporteador", sheet_names)
        self.assertIn(
            "Recomendaciones_Reporteador", sheet_names
        )

    def test_legacy_datamap_remains_supported(self) -> None:
        legacy = {
            "08_Clasificacion_Analitica": pd.DataFrame(
                [
                    {
                        "Variable": "A7",
                        "Variable_Label": "Edad",
                        "Columna_Legacy": "Conservar",
                    }
                ]
            )
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "legacy.xlsx"
            save_final_datamap(path, legacy, self.review)
            exported = pd.read_excel(path, sheet_name=None)

        self.assertIn("08_Clasificacion_Analitica", exported)
        self.assertIn("10_Datamap_Corregido", exported)
        self.assertEqual(
            exported["08_Clasificacion_Analitica"].iloc[0][
                "Columna_Legacy"
            ],
            "Conservar",
        )


if __name__ == "__main__":
    unittest.main()
