from __future__ import annotations

import unittest

import pandas as pd

from src.reporter.charts import build_chart


class ChartLabelTests(unittest.TestCase):
    def test_percentage_chart_displays_one_decimal_labels(
        self,
    ) -> None:
        figure = build_chart(
            "Porcentaje",
            pd.DataFrame(
                {
                    "respuesta": ["Sí", "No"],
                    "banner": ["Total", "Total"],
                    "porcentaje": [0.625, 0.375],
                }
            ),
            "Pregunta",
            has_banner=False,
        )

        self.assertIsNotNone(figure)
        self.assertEqual(
            figure.data[0].texttemplate, "%{text:.1f}%"
        )
        self.assertEqual(
            list(figure.data[0].text), [62.5, 37.5]
        )

    def test_nps_chart_displays_percentage_labels(
        self,
    ) -> None:
        figure = build_chart(
            "NPS",
            pd.DataFrame(
                {
                    "banner": ["Total"],
                    "promotores": [0.5],
                    "pasivos": [0.3],
                    "detractores": [0.2],
                }
            ),
            "NPS",
            has_banner=False,
        )

        self.assertIsNotNone(figure)
        self.assertTrue(
            all(
                trace.texttemplate == "%{text:.1f}%"
                for trace in figure.data
            )
        )

    def test_banner_chart_keeps_total_alongside_segments(
        self,
    ) -> None:
        figure = build_chart(
            "Porcentaje",
            pd.DataFrame(
                {
                    "respuesta": ["Sí", "Sí", "Sí"],
                    "banner": ["Total", "Norte", "Sur"],
                    "porcentaje": [0.50, 0.60, 0.40],
                }
            ),
            "Pregunta",
            has_banner=True,
        )

        self.assertIsNotNone(figure)
        self.assertEqual(
            {trace.name for trace in figure.data},
            {"Total", "Norte", "Sur"},
        )
        self.assertEqual(figure.data[0].name, "Total")
        self.assertEqual(
            figure.data[0].marker.color, "#176B87"
        )

    def test_total_is_first_visual_bar_in_horizontal_groups(
        self,
    ) -> None:
        rows = []
        for response in ["A", "B", "C", "D", "E", "F"]:
            rows.extend(
                [
                    {
                        "respuesta": response,
                        "banner": "Total",
                        "porcentaje": 0.50,
                    },
                    {
                        "respuesta": response,
                        "banner": "Norte",
                        "porcentaje": 0.60,
                    },
                    {
                        "respuesta": response,
                        "banner": "Sur",
                        "porcentaje": 0.40,
                    },
                ]
            )
        figure = build_chart(
            "Porcentaje",
            pd.DataFrame(rows),
            "Pregunta",
            has_banner=True,
        )

        self.assertEqual(figure.data[0].name, "Total")
        self.assertEqual(
            figure.layout.legend.traceorder, "normal"
        )

    def test_horizontal_labels_are_ordered_by_total(
        self,
    ) -> None:
        rows = []
        for response, total in [
            ("Mayor", 0.80),
            ("Intermedia", 0.50),
            ("Menor", 0.10),
            ("Otra", 0.01),
            ("Extra 1", 0.005),
            ("Extra 2", 0.001),
        ]:
            rows.extend(
                [
                    {
                        "respuesta": response,
                        "banner": "Total",
                        "porcentaje": total,
                    },
                    {
                        "respuesta": response,
                        "banner": "Norte",
                        "porcentaje": min(total + 0.05, 1),
                    },
                ]
            )
        figure = build_chart(
            "Porcentaje",
            pd.DataFrame(rows),
            "Pregunta",
            has_banner=True,
        )

        self.assertEqual(
            list(figure.layout.yaxis.categoryarray),
            [
                "Extra 2",
                "Extra 1",
                "Otra",
                "Menor",
                "Intermedia",
                "Mayor",
            ],
        )


if __name__ == "__main__":
    unittest.main()
