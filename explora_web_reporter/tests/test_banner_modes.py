from __future__ import annotations

import unittest

import pandas as pd

from src.reporter.banners import (
    banner_comparison_groups,
    banner_order,
    expand_banner,
)
from src.reporter.significance import percentage_significance


class BannerModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = pd.DataFrame(
            {
                "id_respondente": ["1", "2", "3", "4"],
                "respuesta": ["Sí", "Sí", "No", "No"],
                "_peso": [1.0, 1.0, 1.0, 1.0],
            }
        )
        self.respondents = pd.DataFrame(
            {
                "id_respondente": ["1", "2", "3", "4"],
                "REGION": [1, 1, 2, 2],
                "SEXO": [1, 2, 1, 2],
            }
        )
        self.options = pd.DataFrame(
            [
                {"variable": "REGION", "codigo": 1, "label": "Norte"},
                {"variable": "REGION", "codigo": 2, "label": "Sur"},
                {"variable": "SEXO", "codigo": 1, "label": "Mujer"},
                {"variable": "SEXO", "codigo": 2, "label": "Hombre"},
            ]
        )

    def test_nested_mode_keeps_current_crossed_banner(self) -> None:
        result = expand_banner(
            self.data,
            self.respondents,
            self.options,
            ["REGION", "SEXO"],
            mode="nested",
        )

        categories = set(result["banner"]) - {"Total"}
        self.assertEqual(len(result), 8)
        self.assertIn(
            "REGION: 1 | Norte / SEXO: 1 | Mujer", categories
        )

    def test_separate_mode_builds_independent_banner_blocks(self) -> None:
        result = expand_banner(
            self.data,
            self.respondents,
            self.options,
            ["REGION", "SEXO"],
            mode="separate",
        )

        categories = set(result["banner"]) - {"Total"}
        self.assertEqual(len(result), 12)
        self.assertEqual(
            categories,
            {
                "REGION: 1 | Norte",
                "REGION: 2 | Sur",
                "SEXO: 1 | Mujer",
                "SEXO: 2 | Hombre",
            },
        )
        self.assertFalse(any(" / " in item for item in categories))
        self.assertEqual(
            banner_order(result["banner"]),
            [
                "Total",
                "REGION: 1 | Norte",
                "REGION: 2 | Sur",
                "SEXO: 1 | Mujer",
                "SEXO: 2 | Hombre",
            ],
        )

    def test_significance_only_compares_within_each_separate_banner(
        self,
    ) -> None:
        summary = pd.DataFrame(
            [
                {
                    "banner": banner,
                    "respuesta": "Sí",
                    "n": count,
                    "base": 100,
                    "porcentaje": count,
                }
                for banner, count in (
                    ("REGION: 1 | Norte", 90),
                    ("REGION: 2 | Sur", 10),
                    ("SEXO: 1 | Mujer", 10),
                    ("SEXO: 2 | Hombre", 90),
                )
            ]
        )
        groups = banner_comparison_groups(
            summary["banner"], ["REGION", "SEXO"], "separate"
        )

        result = percentage_significance(
            summary,
            min_base=30,
            comparison_groups=groups,
        ).iloc[0]

        self.assertEqual(result["REGION: 1 | Norte"], "B")
        self.assertEqual(result["REGION: 2 | Sur"], "")
        self.assertEqual(result["SEXO: 1 | Mujer"], "")
        self.assertEqual(result["SEXO: 2 | Hombre"], "C")


if __name__ == "__main__":
    unittest.main()
