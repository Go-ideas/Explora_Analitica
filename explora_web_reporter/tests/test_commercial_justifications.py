from __future__ import annotations

from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import pandas as pd

from src.builder.recommendations_builder import (
    build_recomendaciones_reporteador,
    format_base_distribution,
)
from src.export.datamap_exporter import save_final_datamap


class CommercialJustificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.datamap = pd.DataFrame(
            [
                {
                    "variable": "A2",
                    "label": "Ciudad",
                    "pregunta_id": "A2",
                    "es_banner_recomendado": True,
                    "es_filtro_recomendado": True,
                    "justificacion_banner_filtro": (
                        "Ciudad se recomienda como banner porque "
                        "permite comparar diferencias territoriales "
                        "de forma accionable."
                    ),
                    "uso_comercial_sugerido": (
                        "Comparar resultados por plaza."
                    ),
                }
            ]
        )
        self.banner_sheet = pd.DataFrame(
            [
                {
                    "Variable": "A2",
                    "Variable_Label": "Ciudad",
                    "Rol_Recomendado": "Banner y filtro",
                    "Es_Banner_Recomendado": "Sí",
                    "Es_Filtro_Recomendado": "Sí",
                    "Justificacion": "1.0:300; 2.0:100",
                    "Base_Categorias_Obs": "1.0:300; 2.0:100",
                    "Uso_Comercial_Sugerido": (
                        "Comparar resultados por plaza."
                    ),
                }
            ]
        )
        self.meta = SimpleNamespace(
            variable_value_labels={
                "A2": {
                    1.0: "Ciudad de México",
                    2.0: "Monterrey",
                }
            }
        )

    def test_raw_counts_are_separated_from_justification(
        self,
    ) -> None:
        recommendations = build_recomendaciones_reporteador(
            self.datamap,
            {
                "11_Banners_Filtros_Recomendados": (
                    self.banner_sheet
                )
            },
            df_spss=pd.DataFrame(
                {"A2": [1.0] * 300 + [2.0] * 100}
            ),
            meta_spss=self.meta,
        )
        row = recommendations[
            recommendations["tipo_recomendacion"].eq(
                "banner_filtro"
            )
        ].iloc[0]

        self.assertNotIn("1.0:300", row["justificacion"])
        self.assertIn(
            "diferencias territoriales", row["justificacion"]
        )
        self.assertEqual(
            row["distribucion_base"],
            "Ciudad de México n=300; Monterrey n=100",
        )

    def test_distribution_without_labels_uses_code_names(
        self,
    ) -> None:
        distribution = format_base_distribution(
            pd.Series([1.0, 1.0, 2.0]), {}
        )
        self.assertEqual(
            distribution, "Código 1 n=2; Código 2 n=1"
        )

    def test_final_datamap_exports_clean_separate_fields(
        self,
    ) -> None:
        sheets = {
            "08_Clasificacion_Analitica": pd.DataFrame(
                [{"Variable": "A2"}]
            ),
            "11_Banners_Filtros_Recomendados": self.banner_sheet,
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "Datamap_Final.xlsx"
            save_final_datamap(
                path,
                sheets,
                self.datamap,
                df_spss=pd.DataFrame(
                    {"A2": [1.0] * 300 + [2.0] * 100}
                ),
                meta_spss=self.meta,
            )
            exported = pd.read_excel(
                path,
                sheet_name="11_Banners_Filtros_Recomendados",
            )

        self.assertNotIn(
            "1.0:300", exported.iloc[0]["Justificacion"]
        )
        self.assertEqual(
            exported.iloc[0]["Distribucion_Base"],
            "Ciudad de México n=300; Monterrey n=100",
        )


if __name__ == "__main__":
    unittest.main()
