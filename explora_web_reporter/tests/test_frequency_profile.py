from __future__ import annotations

import unittest

import pandas as pd

from src.reporter.frequency_profile import build_frequency_profile


class FrequencyProfileTests(unittest.TestCase):
    def test_includes_zero_frequency_and_unlabeled_codes(self) -> None:
        series = pd.Series([1.0, 1.0, 2.0, 3.0, None])

        table, summary = build_frequency_profile(
            series,
            value_labels={
                1.0: "Sí",
                2.0: "No",
                4.0: "Otra respuesta",
            },
        )

        frequencies = dict(
            zip(table["Código"], table["Frecuencia"])
        )
        self.assertEqual(frequencies["1"], 2)
        self.assertEqual(frequencies["4"], 0)
        self.assertEqual(frequencies["3"], 1)
        self.assertEqual(frequencies["(vacío)"], 1)
        self.assertEqual(summary.valid, 4)
        self.assertEqual(summary.missing, 1)
        self.assertEqual(summary.unlabeled_codes, 1)
        self.assertEqual(summary.unlabeled_observations, 1)
        self.assertEqual(summary.zero_frequency_labels, 1)

        row_one = table.loc[table["Código"].eq("1")].iloc[0]
        self.assertAlmostEqual(row_one["% válido"], 50.0)

    def test_excludes_defined_missing_from_valid_percentage(self) -> None:
        series = pd.Series([1.0, 1.0, 99.0])

        table, summary = build_frequency_profile(
            series,
            value_labels={1.0: "Sí", 99.0: "No sabe"},
            missing_values={99.0},
        )

        valid_row = table.loc[table["Código"].eq("1")].iloc[0]
        missing_row = table.loc[table["Código"].eq("99")].iloc[0]
        self.assertEqual(summary.valid, 2)
        self.assertEqual(summary.missing, 1)
        self.assertAlmostEqual(valid_row["% válido"], 100.0)
        self.assertTrue(pd.isna(missing_row["% válido"]))
        self.assertEqual(
            missing_row["Estado"], "Perdido definido"
        )


if __name__ == "__main__":
    unittest.main()
