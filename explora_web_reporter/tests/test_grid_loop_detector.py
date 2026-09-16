from __future__ import annotations

from pathlib import Path
import tempfile

import pandas as pd

from src.builder.analytic_db_builder import build_analytic_database
from src.structure.grid_loop_detector import (
    detect_grid_loop_structures,
    enrich_datamap_with_spss_structure,
    validate_grid_loop_children,
)
from src.reporter.multi_metrics import validate_calculations_for_question
from src.reporter.tabulator import available_questions


class Metadata:
    def __init__(self, value_labels=None, variable_labels=None):
        self.variable_value_labels = value_labels or {}
        self.column_names_to_labels = variable_labels or {}


def _type_for(structures: pd.DataFrame, parent: str) -> str:
    selected = structures[
        structures["pregunta_padre"].astype(str).eq(parent)
    ]
    assert not selected.empty
    return str(selected.iloc[0]["tipo_estructura_detectada"])


def test_grid_rm_loop_with_ot_keeps_quantitative_parent() -> None:
    df = pd.DataFrame(
        {
            "I_1_QX_1": [1, 0, None],
            "I_1_QX_2": [0, 2, None],
            "I_2_QX_1": [1, 0, 1],
            "I_2_QX_2": [0, 2, 0],
            "I_1_QX_OT": ["", "otro texto", ""],
            "I_2_QX_OT": ["", "", "otro"],
        }
    )
    meta = Metadata(
        {
            "I_1_QX_1": {1: "Opción A"},
            "I_1_QX_2": {2: "Opción B"},
            "I_2_QX_1": {1: "Opción A"},
            "I_2_QX_2": {2: "Opción B"},
        }
    )
    review = pd.DataFrame(
        {
            "variable": df.columns,
            "clasificacion_analitica": ["Abierta"] * len(df.columns),
        }
    )

    enriched = enrich_datamap_with_spss_structure(review, df, meta)
    structures = enriched.attrs["grid_loop_structures"]

    assert _type_for(structures, "QX") == "GRID_RM/LOOP_RM"
    quantitative = enriched[
        enriched["variable"].astype(str).eq("I_1_QX_1")
    ].iloc[0]
    open_row = enriched[
        enriched["variable"].astype(str).eq("I_1_QX_OT")
    ].iloc[0]
    assert quantitative["clasificacion_analitica"] == "Pregunta analizable"
    assert quantitative["tipo_pregunta"] == "GRID_RM/LOOP_RM"
    assert open_row["clasificacion_analitica"] == "Abierta"
    assert bool(open_row["es_abierta_asociada"])
    assert "QX" in set(enriched["variable"].astype(str))


def test_grid_scale_detection() -> None:
    labels = {
        1: "Nada importante",
        2: "Poco importante",
        3: "Algo importante",
        4: "Importante",
        5: "Muy importante",
    }
    df = pd.DataFrame({"P17_1": [1, 2], "P17_2": [3, 4], "P17_3": [5, 4]})
    meta = Metadata({column: labels for column in df.columns})

    structures = detect_grid_loop_structures(df, meta)

    assert _type_for(structures, "P17") == "GRID_ESCALA"


def test_loop_ru_detection() -> None:
    labels = {1: "Diario", 2: "Semanal", 3: "Mensual", 4: "Ocasional"}
    df = pd.DataFrame({"I_1_QF": [1, 2], "I_2_QF": [2, 3], "I_3_QF": [4, 1]})
    meta = Metadata({column: labels for column in df.columns})

    structures = detect_grid_loop_structures(df, meta)

    assert _type_for(structures, "QF") == "LOOP_RU"


def test_loop_numeric_detection() -> None:
    df = pd.DataFrame(
        {
            "CANAL_1_GASTO": [100.5, 0.0, 33.0],
            "CANAL_2_GASTO": [55.0, 80.0, 0.0],
            "CANAL_3_GASTO": [10.0, 22.0, 31.0],
        }
    )

    structures = detect_grid_loop_structures(df, Metadata())

    assert _type_for(structures, "GASTO") == "LOOP_NUMERICO"


def test_loop_range_detection() -> None:
    labels = {
        1: "Menos de 1 vez",
        2: "1 a 3 veces",
        3: "4 a 6 veces",
        4: "7 o más veces",
    }
    df = pd.DataFrame(
        {
            "I_1_QRANGO": [1, 2, 4],
            "I_2_QRANGO": [2, 3, 4],
            "I_3_QRANGO": [1, 1, 3],
        }
    )
    meta = Metadata({column: labels for column in df.columns})

    structures = detect_grid_loop_structures(df, meta)

    assert _type_for(structures, "QRANGO") == "LOOP_RANGO"


def test_rm_simple_with_ot_detection() -> None:
    df = pd.DataFrame(
        {
            "Q10_1": [1, 0, 1],
            "Q10_2": [0, 2, 2],
            "Q10_3": [0, 0, 3],
            "Q10_OT": ["", "otro", ""],
        }
    )
    meta = Metadata(
        {
            "Q10_1": {1: "Uno"},
            "Q10_2": {2: "Dos"},
            "Q10_3": {3: "Tres"},
        }
    )

    structures = detect_grid_loop_structures(df, meta)

    assert _type_for(structures, "Q10") == "RM_SIMPLE"
    row = structures[
        structures["pregunta_padre"].astype(str).eq("Q10")
    ].iloc[0]
    assert "Q10_OT" in row["variables_abiertas_asociadas"]


def test_pure_open_detection() -> None:
    df = pd.DataFrame({"P29_OT": ["texto", "", "otro texto"]})

    structures = detect_grid_loop_structures(df, Metadata())

    assert _type_for(structures, "P29") == "Abierta"


def test_grid_parent_without_children_blocks_build() -> None:
    df = pd.DataFrame({"Q1": [1, 2, 3]})
    datamap = pd.DataFrame(
        {
            "variable": ["QX_PARENT"],
            "pregunta_id": ["QX"],
            "tipo_pregunta": ["GRID_RM/LOOP_RM"],
            "tipo_estructura_grid": ["GRID_RM"],
            "es_grid": [True],
            "es_grid_rm_loop": [True],
            "es_abierta_asociada": [False],
        }
    )

    validation = validate_grid_loop_children(datamap, df, Metadata())

    assert not validation.empty
    assert bool(validation.iloc[0]["bloquea"])


def test_hc9_like_regression_appears_once_in_selector() -> None:
    df = pd.DataFrame(
        {
            "I_1_HC9_1": [1, 0, None],
            "I_1_HC9_2": [0, 2, None],
            "I_2_HC9_1": [1, 0, 1],
            "I_2_HC9_2": [0, 2, 0],
            "I_1_HC9_OT": ["", "otro texto", ""],
            "I_2_HC9_OT": ["", "", "otro"],
        }
    )
    meta = Metadata(
        {
            "I_1_HC9_1": {1: "Opción A"},
            "I_1_HC9_2": {2: "Opción B"},
            "I_2_HC9_1": {1: "Opción A"},
            "I_2_HC9_2": {2: "Opción B"},
        }
    )
    review = pd.DataFrame(
        {
            "variable": df.columns,
            "label": df.columns,
            "clasificacion_analitica": ["Abierta"] * len(df.columns),
            "usar_en_dashboard": [True] * len(df.columns),
            "es_banner": [False] * len(df.columns),
            "es_filtro": [False] * len(df.columns),
            "es_ponderador": [False] * len(df.columns),
        }
    )
    enriched = enrich_datamap_with_spss_structure(review, df, meta)

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "hc9_like.db"
        build_analytic_database(
            df,
            meta,
            enriched,
            {},
            db_path=db_path,
            export_revision=False,
        )
        questions = available_questions(db_path)

    hc9 = questions[questions["pregunta_id"].astype(str).eq("HC9")]
    assert len(hc9) == 1
    assert hc9.iloc[0]["tipo_pregunta_reporter"] == "GRID_RM/LOOP_RM"
    assert not questions["pregunta_id"].astype(str).str.contains("OT").any()


def test_grid_rm_rejects_scale_only_metrics() -> None:
    valid, warnings = validate_calculations_for_question(
        "GRID_RM/LOOP_RM grid_rm loop_rm multirrespuesta agrupada __rm__",
        ["% respondentes", "Media", "Top2Box", "NPS"],
    )

    assert valid == ["% respondentes"]
    assert any("Media no aplica" in warning for warning in warnings)
    assert any("Top2Box no aplica" in warning for warning in warnings)
    assert any("NPS no aplica" in warning for warning in warnings)
