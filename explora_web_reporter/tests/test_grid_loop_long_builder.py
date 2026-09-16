from __future__ import annotations

import pandas as pd

from src.builder.grid_loop_long_builder import build_grid_loop_long


class Metadata:
    variable_value_labels = {}


def test_grid_rm_base_is_reconstructed_from_entity_option_set() -> None:
    df = pd.DataFrame(
        {
            "BRAND_A_REASON_1": [1, pd.NA, 0, pd.NA],
            "BRAND_A_REASON_2": [pd.NA, 2, 0, pd.NA],
        }
    )
    respondentes = pd.DataFrame(
        {
            "id_respondente": ["R1", "R2", "R3", "R4"],
        }
    )
    datamap = pd.DataFrame(
        [
            {
                "variable": "BRAND_A_REASON_1",
                "pregunta_id": "HC9",
                "grid_id": "HC9",
                "pregunta_padre": "HC9",
                "tipo_pregunta": "GRID_RM/LOOP_RM",
                "tipo_estructura_grid": "GRID_RM",
                "clasificacion_analitica": "Pregunta analizable",
                "es_ponderador": False,
                "es_grid_rm_loop": True,
                "entidad_loop": "Brand A",
                "codigo_opcion_rm": "1",
                "label_opcion_rm": "Precio",
            },
            {
                "variable": "BRAND_A_REASON_2",
                "pregunta_id": "HC9",
                "grid_id": "HC9",
                "pregunta_padre": "HC9",
                "tipo_pregunta": "GRID_RM/LOOP_RM",
                "tipo_estructura_grid": "GRID_RM",
                "clasificacion_analitica": "Pregunta analizable",
                "es_ponderador": False,
                "es_grid_rm_loop": True,
                "entidad_loop": "Brand A",
                "codigo_opcion_rm": "2",
                "label_opcion_rm": "Calidad",
            },
        ]
    )

    result = build_grid_loop_long(df, Metadata(), datamap, respondentes)

    r1_price = result[
        (result["id_respondente"] == "R1")
        & (result["label_opcion"] == "Precio")
    ].iloc[0]
    r1_quality = result[
        (result["id_respondente"] == "R1")
        & (result["label_opcion"] == "Calidad")
    ].iloc[0]
    r4 = result[result["id_respondente"] == "R4"]

    assert r1_price["seleccionado"] == 1
    assert r1_quality["seleccionado"] == 0
    assert r1_quality["base_valida"] == 1
    assert r1_quality["missing_estructural"] == 0
    assert r4["base_valida"].sum() == 0
    assert r4["missing_estructural"].sum() == 2
