from __future__ import annotations

import unittest

import pandas as pd

from src.export.pivot_exporter import build_pivot_table


class PivotExporterTests(unittest.TestCase):
    def test_duplicate_respondent_lookup_does_not_expand_pivot(self) -> None:
        tables = {
            "preguntas": pd.DataFrame(
                [
                    {
                        "pregunta_id": "Q1",
                        "texto_pregunta": "Pregunta",
                        "tipo_calculo": "Frecuencia",
                    }
                ]
            ),
            "respondentes": pd.DataFrame(
                {
                    "id_respondente": ["1", "1"],
                    "CIUDAD": ["Norte", "Sur"],
                }
            ),
            "configuracion_dashboard": pd.DataFrame(
                [
                    {
                        "tipo_configuracion": "banner",
                        "variable": "CIUDAD",
                    }
                ]
            ),
            "respuestas_long": pd.DataFrame(
                {
                    "id_respondente": ["1", "1"],
                    "pregunta_id": ["Q1", "Q1"],
                    "variable": ["P1", "P1"],
                    "codigo_respuesta": [1, 2],
                    "respuesta_label": ["Si", "No"],
                    "valor_numerico": [1, 2],
                    "ponderador": [1.0, 1.0],
                }
            ),
        }

        result = build_pivot_table(tables)

        self.assertEqual(len(result), 2)
        self.assertEqual(result["CIUDAD"].tolist(), ["Norte", "Norte"])


if __name__ == "__main__":
    unittest.main()
