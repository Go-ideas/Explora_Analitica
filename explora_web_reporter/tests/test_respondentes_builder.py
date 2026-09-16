from __future__ import annotations

import unittest

import pandas as pd

from src.builder.respondentes_builder import build_respondentes


class RespondentesBuilderTests(unittest.TestCase):
    def test_invalid_detected_id_uses_unique_internal_ids(self) -> None:
        df_spss = pd.DataFrame(
            {
                "ParentID": [float("nan"), float("nan"), float("nan")],
                "CIUDAD": [1, 2, 3],
            }
        )
        datamap = pd.DataFrame(
            {
                "variable": ["CIUDAD"],
                "clasificacion_analitica": ["Banner"],
                "es_banner": [True],
            }
        )

        result = build_respondentes(df_spss, datamap)

        self.assertEqual(
            result["id_respondente"].tolist(),
            ["R000001", "R000002", "R000003"],
        )
        self.assertTrue(result["id_respondente"].is_unique)
        self.assertIn("CIUDAD", result.columns)

    def test_unique_detected_id_is_preserved(self) -> None:
        df_spss = pd.DataFrame({"ParentID": ["A", "B", "C"]})

        result = build_respondentes(df_spss, pd.DataFrame())

        self.assertEqual(
            result["id_respondente"].tolist(), ["A", "B", "C"]
        )
        self.assertEqual(result["id_original"].tolist(), ["A", "B", "C"])

    def test_unsafe_banner_attribute_is_not_copied(self) -> None:
        df_spss = pd.DataFrame(
            {
                "ParentID": [float("nan"), float("nan")],
                "SEGMENTO": ["A", "B"],
            }
        )
        datamap = pd.DataFrame(
            [
                {
                    "variable": "ParentID",
                    "clasificacion_analitica": "Banner",
                    "es_banner": True,
                },
                {
                    "variable": "SEGMENTO",
                    "clasificacion_analitica": "Banner",
                    "es_banner": True,
                },
            ]
        )

        result = build_respondentes(df_spss, datamap)

        self.assertNotIn("ParentID", result.columns)
        self.assertIn("SEGMENTO", result.columns)


if __name__ == "__main__":
    unittest.main()
