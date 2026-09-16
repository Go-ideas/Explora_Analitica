from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

import pandas as pd

from src.utils.text_utils import find_column, normalize_text, truthy


STRUCTURE_COLUMNS = [
    "pregunta_padre",
    "grid_id",
    "tipo_estructura_detectada",
    "filas_detectadas",
    "columnas_detectadas",
    "variables_numericas",
    "variables_texto",
    "variables_abiertas_asociadas",
    "formato_valores",
    "value_label_patron",
    "valores_observados_patron",
    "base_valida_db",
    "base_valida_pregunta_padre",
    "base_valida_por_fila",
    "base_valida_por_columna",
    "regla_base_valida",
    "variables_base_valida",
    "evidencia_base_valida",
    "riesgo_base_valida",
    "evidencia_nombre_variable",
    "evidencia_label_spss",
    "evidencia_value_labels",
    "evidencia_valores_observados",
    "evidencia_datamap",
    "nivel_confianza",
    "riesgo",
    "accion_recomendada",
]

CHILD_COLUMNS = [
    "variable",
    "pregunta_padre",
    "grid_id",
    "tipo_estructura_grid",
    "es_grid",
    "es_item_grid",
    "es_grid_rm_loop",
    "entidad_loop",
    "orden_entidad_loop",
    "label_entidad_loop",
    "codigo_opcion_rm",
    "label_opcion_rm",
    "orden_opcion_rm",
    "formato_rm",
    "value_label_patron",
    "valores_observados_patron",
    "es_abierta_asociada",
    "base_valida_pregunta_padre",
    "base_valida_fila",
    "base_valida_columna",
    "regla_base_valida",
]


@dataclass(frozen=True)
class VariableEvidence:
    variable: str
    parent: str
    entity: str
    option: str
    label: str
    labels: dict[Any, str]
    observed: set[Any]
    numeric: bool
    open_associated: bool
    value_pattern: str


def detect_grid_loop_structures(
    df_spss,
    meta_spss,
    datamap_df=None,
    datamap_sheets=None,
):
    """Detect fila x columna structures from SPSS evidence and Datamap hints."""
    del datamap_sheets
    if df_spss is None or df_spss.empty:
        return pd.DataFrame(columns=STRUCTURE_COLUMNS)

    datamap_lookup = _datamap_lookup(datamap_df)
    evidences = [
        _variable_evidence(variable, df_spss, meta_spss, datamap_lookup)
        for variable in df_spss.columns
    ]
    groups: dict[str, list[VariableEvidence]] = {}
    for evidence in evidences:
        if evidence.parent:
            groups.setdefault(evidence.parent, []).append(evidence)

    rows = []
    child_rows = []
    for parent, items in groups.items():
        if len(items) < 2 and not any(item.open_associated for item in items):
            continue
        result = _classify_group(parent, items, datamap_lookup)
        if not result:
            continue
        rows.append(result)
        child_rows.extend(_child_records(items, result))

    structures = pd.DataFrame(rows, columns=STRUCTURE_COLUMNS)
    children = pd.DataFrame(child_rows, columns=CHILD_COLUMNS)
    structures.attrs["grid_loop_children"] = children
    return structures


def enrich_datamap_with_spss_structure(
    review,
    df_spss,
    meta_spss,
    datamap_sheets=None,
):
    """Return review Datamap enriched with detected SPSS grid/loop structure."""
    if review is None:
        return review
    result = review.copy()
    structures = detect_grid_loop_structures(
        df_spss,
        meta_spss,
        datamap_df=result,
        datamap_sheets=datamap_sheets,
    )
    children = structures.attrs.get(
        "grid_loop_children", pd.DataFrame(columns=CHILD_COLUMNS)
    )
    result.attrs["grid_loop_structures"] = structures
    result.attrs["grid_loop_children"] = children
    for column in CHILD_COLUMNS:
        if column != "variable" and column not in result:
            result[column] = "" if not column.startswith("es_") else False
    if children.empty or "variable" not in result:
        return result

    child_lookup = (
        children.drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
    )
    for index, row in result.iterrows():
        variable = str(row.get("variable") or "").strip()
        child = child_lookup.get(variable)
        if not child:
            continue
        for column in CHILD_COLUMNS:
            if column == "variable":
                continue
            value = child.get(column)
            if _has_value(value):
                result.at[index, column] = value
        parent_id = _first_text(child.get("grid_id"), child.get("pregunta_padre"))
        if parent_id:
            result.at[index, "pregunta_id"] = parent_id
            result.at[index, "numero_pregunta"] = parent_id
        structure = str(child.get("tipo_estructura_grid") or "")
        if structure == "GRID_RM/LOOP_RM":
            result.at[index, "tipo_pregunta"] = "GRID_RM/LOOP_RM"
            result.at[index, "tipo_calculo"] = "Multirrespuesta agrupada"
            if _is_open_variable(variable, row.get("label")):
                result.at[index, "clasificacion_analitica"] = "Abierta"
                result.at[index, "usar_en_dashboard"] = False
            else:
                current = str(row.get("clasificacion_analitica") or "")
                if normalize_text(current) in {
                    "abierta",
                    "no_usar_en_dashboard",
                    "requiere_validacion",
                    "",
                }:
                    result.at[index, "clasificacion_analitica"] = (
                        "Pregunta analizable"
                    )
                result.at[index, "usar_en_dashboard"] = True
        elif structure == "GRID_ESCALA":
            result.at[index, "tipo_pregunta"] = "GRID_ESCALA"
            if not _is_open_variable(variable, row.get("label")):
                result.at[index, "clasificacion_analitica"] = (
                    "Pregunta analizable"
                )
                result.at[index, "usar_en_dashboard"] = True
        elif structure in {"LOOP_RU", "LOOP_NUMERICO", "LOOP_RANGO"}:
            result.at[index, "tipo_pregunta"] = structure
            if structure == "LOOP_NUMERICO":
                result.at[index, "tipo_calculo"] = "Media"
        elif structure == "Abierta":
            result.at[index, "tipo_pregunta"] = "Abierta"
            result.at[index, "tipo_calculo"] = "Texto abierto"
            result.at[index, "clasificacion_analitica"] = "Abierta"
            result.at[index, "usar_en_dashboard"] = False
    result = _ensure_parent_rows(result, structures, children)
    result.attrs["grid_loop_structures"] = structures
    result.attrs["grid_loop_children"] = children
    return result


def _ensure_parent_rows(
    review: pd.DataFrame,
    structures: pd.DataFrame,
    children: pd.DataFrame,
) -> pd.DataFrame:
    if structures.empty or "variable" not in review:
        return review
    existing_variables = {
        str(value).strip()
        for value in review["variable"].dropna().astype(str)
    }
    additions = []
    for _, structure in structures.iterrows():
        detected = str(
            structure.get("tipo_estructura_detectada") or ""
        ).strip()
        if detected == "Abierta":
            continue
        parent = _first_text(
            structure.get("grid_id"), structure.get("pregunta_padre")
        )
        if not parent or parent in existing_variables:
            continue
        row = {column: "" for column in review.columns}
        row.update(
            {
                "variable": parent,
                "label": _parent_text(parent, structure, children),
                "pregunta_id": parent,
                "numero_pregunta": parent,
                "texto_pregunta": _parent_text(parent, structure, children),
                "tipo_pregunta": detected,
                "clasificacion_analitica": "Pregunta padre grid",
                "tipo_calculo": _parent_calculation(detected),
                "usar_en_dashboard": True,
                "es_banner": False,
                "es_filtro": False,
                "es_ponderador": False,
                "pregunta_padre": parent,
                "grid_id": parent,
                "tipo_estructura_grid": detected,
                "es_grid": True,
                "es_item_grid": False,
                "es_grid_rm_loop": detected == "GRID_RM/LOOP_RM",
                "base_valida_pregunta_padre": structure.get(
                    "base_valida_pregunta_padre", ""
                ),
                "regla_base_valida": structure.get(
                    "regla_base_valida", ""
                ),
            }
        )
        additions.append(row)
        existing_variables.add(parent)
    if not additions:
        return review
    return pd.concat(
        [review, pd.DataFrame(additions)],
        ignore_index=True,
        sort=False,
    )


def _parent_text(
    parent: str,
    structure: pd.Series,
    children: pd.DataFrame,
) -> str:
    selected = children[
        children.get("grid_id", pd.Series(dtype=str)).astype(str).eq(parent)
        | children.get("pregunta_padre", pd.Series(dtype=str)).astype(str).eq(parent)
    ]
    if not selected.empty and "label_entidad_loop" in selected:
        label = _first_text(*selected["label_entidad_loop"].tolist())
        if label:
            return f"{parent} | {structure.get('tipo_estructura_detectada')}"
    return _first_text(
        structure.get("texto_pregunta"),
        f"{parent} | {structure.get('tipo_estructura_detectada')}",
    )


def _parent_calculation(structure: str) -> str:
    if structure == "GRID_RM/LOOP_RM":
        return "% respondentes"
    if structure == "GRID_ESCALA":
        return "Distribución grid"
    if structure == "LOOP_NUMERICO":
        return "Media"
    if structure in {"RM_SIMPLE", "LOOP_RU"}:
        return "% respondentes" if structure == "RM_SIMPLE" else "Frecuencia"
    return "Frecuencia"


def validate_grid_loop_children(
    datamap_df,
    df_spss,
    meta_spss,
):
    """Validate parent grid/loop questions have real SPSS children."""
    del meta_spss
    columns = [
        "pregunta_padre",
        "nivel",
        "motivo",
        "accion_recomendada",
        "bloquea",
    ]
    if datamap_df is None or datamap_df.empty:
        return pd.DataFrame(columns=columns)
    rows = []
    work = datamap_df.copy()
    for column in (
        "variable",
        "pregunta_id",
        "pregunta_padre",
        "grid_id",
        "tipo_pregunta",
        "tipo_estructura_grid",
        "es_grid",
        "es_item_grid",
        "es_grid_rm_loop",
        "es_abierta_asociada",
    ):
        if column not in work:
            work[column] = ""
    grid_mask = (
        work["es_grid"].apply(truthy)
        | work["es_item_grid"].apply(truthy)
        | work["es_grid_rm_loop"].apply(truthy)
        | work["tipo_pregunta"].map(normalize_text).str.contains(
            "grid|loop", regex=True, na=False
        )
        | work["tipo_estructura_grid"].map(normalize_text).str.contains(
            "grid|loop", regex=True, na=False
        )
    )
    grid_rows = work[grid_mask].copy()
    if grid_rows.empty:
        return pd.DataFrame(columns=columns)
    grid_rows["_parent"] = grid_rows.apply(_parent_from_row, axis=1)
    for parent, group in grid_rows.groupby("_parent", sort=False):
        if not parent:
            continue
        quantitative = group[
            ~group["es_abierta_asociada"].apply(truthy)
            & group["variable"].astype(str).isin(df_spss.columns)
        ]
        structure_text = " ".join(
            group["tipo_pregunta"].astype(str).tolist()
            + group["tipo_estructura_grid"].astype(str).tolist()
        )
        is_grid_rm = "grid_rm" in normalize_text(
            structure_text
        ) or "loop_rm" in normalize_text(structure_text)
        if quantitative.empty:
            rows.append(
                {
                    "pregunta_padre": parent,
                    "nivel": "Crítico",
                    "motivo": (
                        "Pregunta padre grid/loop sin variables hijas "
                        "reales en SPSS."
                    ),
                    "accion_recomendada": (
                        "Revisar mapeo de variables hijas o reclasificar "
                        "la pregunta antes de construir."
                    ),
                    "bloquea": True,
                }
            )
        elif is_grid_rm and not _has_selectable_variables(
            quantitative, df_spss
        ):
            rows.append(
                {
                    "pregunta_padre": parent,
                    "nivel": "Crítico",
                    "motivo": "GRID_RM/LOOP_RM sin variables seleccionables.",
                    "accion_recomendada": (
                        "Validar value labels y valores observados de "
                        "las opciones seleccionables."
                    ),
                    "bloquea": True,
                }
            )
        elif group["es_abierta_asociada"].apply(truthy).any():
            rows.append(
                {
                    "pregunta_padre": parent,
                    "nivel": "Advertencia",
                    "motivo": "Campos OT/Otro asociados a pregunta cuantitativa.",
                    "accion_recomendada": (
                        "Mantenerlos en abiertas; no usarlos para base "
                        "válida principal."
                    ),
                    "bloquea": False,
                }
            )
    return pd.DataFrame(rows, columns=columns)


def question_has_grid_rm_children(
    question_id,
    df_spss,
    meta_spss,
    datamap_df=None,
):
    """Defensive detection of GRID_RM/LOOP_RM children for a question."""
    structures = detect_grid_loop_structures(
        df_spss, meta_spss, datamap_df=datamap_df
    )
    if structures.empty:
        return False
    selected = structures[
        structures["pregunta_padre"].astype(str).eq(str(question_id))
        | structures["grid_id"].astype(str).eq(str(question_id))
    ]
    return bool(
        not selected.empty
        and selected["tipo_estructura_detectada"]
        .astype(str)
        .eq("GRID_RM/LOOP_RM")
        .any()
    )


def _classify_group(
    parent: str,
    items: list[VariableEvidence],
    datamap_lookup: dict[str, dict],
) -> dict[str, Any] | None:
    numeric = [item for item in items if item.numeric and not item.open_associated]
    open_items = [item for item in items if item.open_associated]
    if len(numeric) < 2 and not open_items:
        return None
    if not numeric and open_items:
        return {
            "pregunta_padre": parent,
            "grid_id": parent,
            "tipo_estructura_detectada": "Abierta",
            "filas_detectadas": "",
            "columnas_detectadas": "",
            "variables_numericas": "",
            "variables_texto": ", ".join(item.variable for item in open_items),
            "variables_abiertas_asociadas": "",
            "formato_valores": "texto",
            "value_label_patron": "",
            "valores_observados_patron": "",
            "base_valida_db": "",
            "base_valida_pregunta_padre": "",
            "base_valida_por_fila": "",
            "base_valida_por_columna": "",
            "regla_base_valida": "Variable abierta principal.",
            "variables_base_valida": "",
            "evidencia_base_valida": "Solo existen campos abiertos.",
            "riesgo_base_valida": "",
            "evidencia_nombre_variable": _join_unique(
                item.variable for item in open_items
            ),
            "evidencia_label_spss": _join_unique(
                item.label for item in open_items
            ),
            "evidencia_value_labels": "",
            "evidencia_valores_observados": "",
            "evidencia_datamap": _datamap_evidence(
                parent, open_items, datamap_lookup
            ),
            "nivel_confianza": "Alta",
            "riesgo": "",
            "accion_recomendada": "Tratar como abierta principal.",
        }

    label_sets = [_label_signature(item.labels) for item in numeric]
    shared_labels = len(set(label_sets)) == 1 and bool(label_sets) and bool(label_sets[0])
    unitary_labels = bool(numeric) and all(len(item.labels) == 1 for item in numeric)
    selectable = [item for item in numeric if _is_selectable_pattern(item)]
    scale_like = shared_labels and _labels_look_like_scale(numeric[0].labels)
    range_like = shared_labels and _labels_look_like_range(numeric[0].labels)
    loop_context = _has_loop_context(numeric)
    category_shared = shared_labels and not scale_like
    continuous_numeric = bool(numeric) and all(
        not item.labels and item.value_pattern == "continuo" for item in numeric
    )

    if unitary_labels and selectable and (loop_context or len(_entities(numeric)) > 1):
        structure = "GRID_RM/LOOP_RM"
        metrics = "% respondentes, menciones, % menciones"
    elif scale_like:
        structure = "GRID_ESCALA"
        metrics = "Distribución, media, Top2Box, BottomBox"
    elif range_like and loop_context:
        structure = "LOOP_RANGO"
        metrics = "Distribución de rangos por entidad"
    elif category_shared and loop_context:
        structure = "LOOP_RU"
        metrics = "Distribución por entidad"
    elif continuous_numeric and loop_context:
        structure = "LOOP_NUMERICO"
        metrics = "Media, mediana, rangos"
    elif unitary_labels and selectable:
        structure = "RM_SIMPLE"
        metrics = "% respondentes, menciones, % menciones"
    else:
        return None

    confidence = "Alta" if (
        (unitary_labels and selectable) or scale_like or category_shared
    ) else "Probable"
    base_ids = _base_ids(numeric)
    risk = _risk_message(structure, numeric, open_items, confidence)
    return {
        "pregunta_padre": parent,
        "grid_id": parent,
        "tipo_estructura_detectada": structure,
        "filas_detectadas": ", ".join(_entities(numeric)),
        "columnas_detectadas": ", ".join(_options(numeric)),
        "variables_numericas": ", ".join(item.variable for item in numeric),
        "variables_texto": ", ".join(
            item.variable for item in items if not item.numeric
        ),
        "variables_abiertas_asociadas": ", ".join(
            item.variable for item in open_items
        ),
        "formato_valores": _join_unique(item.value_pattern for item in numeric),
        "value_label_patron": (
            "Compartido" if shared_labels else "Unitario por opción" if unitary_labels else "Mixto"
        ),
        "valores_observados_patron": _join_unique(
            _observed_signature(item.observed) for item in numeric
        ),
        "base_valida_db": len(base_ids),
        "base_valida_pregunta_padre": len(base_ids),
        "base_valida_por_fila": "",
        "base_valida_por_columna": "",
        "regla_base_valida": (
            "Missing/NaN = fuera de base; 0 = no seleccionado; "
            "código/1/Sí = seleccionado."
            if structure in {"GRID_RM/LOOP_RM", "RM_SIMPLE"}
            else "Base inferida por valores válidos de variables hijas."
        ),
        "variables_base_valida": ", ".join(item.variable for item in numeric),
        "evidencia_base_valida": "Valores observados no missing en hijas cuantitativas.",
        "riesgo_base_valida": "Probable" if confidence != "Alta" else "",
        "evidencia_nombre_variable": _join_unique(
            item.variable for item in numeric[:5]
        ),
        "evidencia_label_spss": _join_unique(item.label for item in numeric[:5]),
        "evidencia_value_labels": _join_unique(
            _labels_text(item.labels) for item in numeric[:5]
        ),
        "evidencia_valores_observados": _join_unique(
            _observed_signature(item.observed) for item in numeric[:5]
        ),
        "evidencia_datamap": _datamap_evidence(parent, numeric, datamap_lookup),
        "nivel_confianza": confidence,
        "riesgo": risk,
        "accion_recomendada": _action_for(structure, metrics, risk),
    }


def _child_records(
    items: list[VariableEvidence],
    structure: dict[str, Any],
) -> list[dict[str, Any]]:
    rows = []
    struct_type = structure["tipo_estructura_detectada"]
    base = structure["base_valida_pregunta_padre"]
    for item in items:
        is_open = item.open_associated and bool(
            structure["variables_numericas"]
        )
        rows.append(
            {
                "variable": item.variable,
                "pregunta_padre": structure["pregunta_padre"],
                "grid_id": structure["grid_id"],
                "tipo_estructura_grid": struct_type,
                "es_grid": struct_type
                in {
                    "GRID_RM/LOOP_RM",
                    "GRID_ESCALA",
                    "LOOP_RU",
                    "LOOP_NUMERICO",
                    "LOOP_RANGO",
                },
                "es_item_grid": not is_open,
                "es_grid_rm_loop": struct_type == "GRID_RM/LOOP_RM",
                "entidad_loop": item.entity,
                "orden_entidad_loop": _numeric_part(item.entity),
                "label_entidad_loop": item.entity,
                "codigo_opcion_rm": item.option,
                "label_opcion_rm": _single_label(item.labels) or item.option,
                "orden_opcion_rm": _numeric_part(item.option),
                "formato_rm": item.value_pattern,
                "value_label_patron": structure["value_label_patron"],
                "valores_observados_patron": _observed_signature(item.observed),
                "es_abierta_asociada": is_open,
                "base_valida_pregunta_padre": base,
                "base_valida_fila": "",
                "base_valida_columna": "",
                "regla_base_valida": structure["regla_base_valida"],
            }
        )
    return rows


def _variable_evidence(
    variable: str,
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_lookup: dict[str, dict],
) -> VariableEvidence:
    row = datamap_lookup.get(variable, {})
    labels = _value_labels(meta_spss, variable)
    label = _first_text(
        row.get("label"),
        row.get("texto_pregunta"),
        _variable_label(meta_spss, variable),
    )
    parsed = _parse_variable_name(variable)
    parent = _first_text(
        row.get("grid_id"),
        row.get("pregunta_padre"),
        row.get("pregunta_id"),
        row.get("numero_pregunta"),
        parsed["parent"],
    )
    series = df_spss[variable]
    numeric = pd.api.types.is_numeric_dtype(series) or (
        pd.to_numeric(series.dropna(), errors="coerce").notna().all()
        if series.dropna().size
        else False
    )
    observed = set(series.dropna().unique().tolist())
    open_associated = _is_open_variable(variable, label)
    return VariableEvidence(
        variable=variable,
        parent=parent,
        entity=_first_text(row.get("entidad_loop"), parsed["entity"]),
        option=_first_text(row.get("codigo_opcion_rm"), parsed["option"]),
        label=label,
        labels=labels,
        observed=observed,
        numeric=numeric,
        open_associated=open_associated,
        value_pattern=_value_pattern(observed, labels, numeric),
    )


def _parse_variable_name(variable: str) -> dict[str, str]:
    text = str(variable)
    tokens = [token for token in re.split(r"[_\-\s]+", text) if token]
    if len(tokens) >= 4 and normalize_text(tokens[0]) == "i":
        return {"parent": tokens[2], "entity": tokens[1], "option": tokens[3]}
    if len(tokens) == 3 and normalize_text(tokens[0]) == "i":
        return {"parent": tokens[2], "entity": tokens[1], "option": ""}
    if (
        len(tokens) >= 3
        and re.fullmatch(r"\d+", tokens[1])
        and not _looks_option_token(tokens[-1])
    ):
        return {
            "parent": tokens[-1],
            "entity": "_".join(tokens[:-1]),
            "option": "",
        }
    if len(tokens) >= 2 and _is_open_token(tokens[-1]):
        return {
            "parent": _parent_from_tokens(tokens[:-1]),
            "entity": tokens[-2] if len(tokens) > 2 else "",
            "option": tokens[-1],
        }
    if len(tokens) >= 3 and _looks_option_token(tokens[-1]):
        return {
            "parent": _parent_from_tokens(tokens[:-1]),
            "entity": tokens[-2],
            "option": tokens[-1],
        }
    if len(tokens) == 2 and _looks_option_token(tokens[-1]):
        return {"parent": tokens[0], "entity": "", "option": tokens[1]}
    if len(tokens) >= 2:
        return {
            "parent": _parent_from_tokens(tokens[:-1]),
            "entity": tokens[-1],
            "option": tokens[-1],
        }
    match = re.match(r"([A-Za-z]+\d+)[_]?(\d+|[A-Za-z])$", text)
    if match:
        return {"parent": match.group(1), "entity": match.group(2), "option": match.group(2)}
    return {"parent": text, "entity": "", "option": ""}


def _parent_from_tokens(tokens: list[str]) -> str:
    if not tokens:
        return ""
    if len(tokens) >= 2 and normalize_text(tokens[0]) == "i":
        return tokens[1]
    return "_".join(tokens)


def _datamap_lookup(datamap_df: pd.DataFrame | None) -> dict[str, dict]:
    if datamap_df is None or datamap_df.empty or "variable" not in datamap_df:
        return {}
    return (
        datamap_df.dropna(subset=["variable"])
        .drop_duplicates("variable")
        .set_index("variable")
        .to_dict("index")
    )


def _parent_from_row(row: pd.Series) -> str:
    return _first_text(
        row.get("grid_id"),
        row.get("pregunta_padre"),
        row.get("pregunta_id"),
    )


def _is_open_variable(variable: object, label: object = "") -> bool:
    text = normalize_text(f"{variable} {label}")
    return bool(
        re.search(
            r"(^|_)ot($|_)|otro|otra|other|specify|especificar|cual|cuál|abierta|open_end",
            text,
        )
    )


def _is_open_token(token: str) -> bool:
    return normalize_text(token) in {
        "ot",
        "otro",
        "otra",
        "other",
        "specify",
        "especificar",
    }


def _looks_option_token(token: str) -> bool:
    return bool(re.search(r"\d+$", token)) or normalize_text(token).startswith("op")


def _value_labels(meta_spss: Any, variable: str) -> dict[Any, str]:
    labels = getattr(meta_spss, "variable_value_labels", {}) or {}
    return labels.get(variable, {}) or {}


def _variable_label(meta_spss: Any, variable: str) -> str:
    labels = getattr(meta_spss, "column_names_to_labels", {}) or {}
    return labels.get(variable, "")


def _value_pattern(observed: set[Any], labels: dict[Any, str], numeric: bool) -> str:
    numeric_values = {
        float(value)
        for value in pd.to_numeric(pd.Series(list(observed)), errors="coerce").dropna()
    }
    label_codes = {
        float(value)
        for value in pd.to_numeric(pd.Series(list(labels.keys())), errors="coerce").dropna()
    }
    if not numeric:
        norm = {normalize_text(value) for value in observed}
        if norm.issubset({"si", "sí", "yes", "seleccionado", "no", "no_seleccionado"}):
            return "si_no"
        return "texto"
    if numeric_values.issubset({0.0, 1.0}):
        return "0/1"
    if len(label_codes) == 1 and numeric_values.issubset(label_codes | {0.0}):
        return "0/codigo"
    if len(label_codes) == 1 and numeric_values.issubset(label_codes):
        return "codigo/missing"
    if labels:
        return "categorico"
    return "continuo"


def _is_selectable_pattern(item: VariableEvidence) -> bool:
    return item.value_pattern in {"0/1", "0/codigo", "codigo/missing", "si_no"}


def _labels_look_like_scale(labels: dict[Any, str]) -> bool:
    if len(labels) < 3:
        return False
    text = normalize_text(" ".join(str(value) for value in labels.values()))
    hints = [
        "acuerdo",
        "importante",
        "satisf",
        "frecuente",
        "probable",
        "intencion",
        "intención",
        "recomend",
        "nada",
        "mucho",
        "muy",
        "bipolar",
    ]
    return any(hint in text for hint in hints)


def _labels_look_like_range(labels: dict[Any, str]) -> bool:
    if len(labels) < 2:
        return False
    values = [normalize_text(value) for value in labels.values()]
    text = " ".join(values)
    range_hints = (
        "menos_de",
        "mas_de",
        "o_mas",
        "hasta",
        "entre",
        "_a_",
        "-",
    )
    has_range_words = any(hint in text for hint in range_hints)
    has_numeric_breaks = sum(
        1 for value in values if re.search(r"\d", value)
    ) >= 2
    return has_range_words and has_numeric_breaks


def _has_loop_context(items: list[VariableEvidence]) -> bool:
    entities = [item.entity for item in items if item.entity]
    return len(set(entities)) > 1


def _entities(items: list[VariableEvidence]) -> list[str]:
    values = [item.entity for item in items if item.entity]
    return list(dict.fromkeys(values))


def _options(items: list[VariableEvidence]) -> list[str]:
    values = [
        _single_label(item.labels) or item.option
        for item in items
        if _single_label(item.labels) or item.option
    ]
    return list(dict.fromkeys(values))


def _base_ids(items: list[VariableEvidence]) -> set[int]:
    # Detection summary uses a structural base count. Runtime reports compute
    # exact respondent bases from SQLite/SPSS after filters and banners.
    return set(range(max((len(item.observed) for item in items), default=0)))


def _has_selectable_variables(group: pd.DataFrame, df_spss: pd.DataFrame) -> bool:
    for variable in group["variable"].astype(str):
        if variable not in df_spss:
            continue
        values = pd.to_numeric(
            df_spss[variable].dropna(), errors="coerce"
        ).dropna()
        unique = set(values.unique().tolist())
        if unique and (unique - {0}) and (
            unique.issubset({0, 1}) or 0 in unique or len(unique) == 1
        ):
            return True
    return False


def _risk_message(
    structure: str,
    numeric: list[VariableEvidence],
    open_items: list[VariableEvidence],
    confidence: str,
) -> str:
    risks = []
    if confidence != "Alta":
        risks.append("Requiere revisión")
    if open_items and numeric:
        risks.append("OT/Otro asociado; no reclasificar pregunta padre como abierta")
    if structure == "GRID_ESCALA" and not numeric:
        risks.append("Grid sin ítems numéricos suficientes")
    return "; ".join(risks)


def _action_for(structure: str, metrics: str, risk: str) -> str:
    action = f"Tabular como {structure}. Métricas válidas: {metrics}."
    if risk:
        action += " Revisar riesgos documentados antes de exportar."
    return action


def _datamap_evidence(
    parent: str,
    items: list[VariableEvidence],
    datamap_lookup: dict[str, dict],
) -> str:
    values = []
    for item in items:
        row = datamap_lookup.get(item.variable, {})
        values.append(
            _first_text(
                row.get("tipo_pregunta"),
                row.get("tipo_estructura_grid"),
                row.get("clasificacion_analitica"),
            )
        )
    return _join_unique([parent, *values])


def _label_signature(labels: dict[Any, str]) -> str:
    return "|".join(
        f"{key}:{value}"
        for key, value in sorted(labels.items(), key=lambda item: str(item[0]))
    )


def _labels_text(labels: dict[Any, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in labels.items())


def _observed_signature(values: set[Any]) -> str:
    normalized = sorted(str(value) for value in values)
    return ", ".join(normalized[:12])


def _single_label(labels: dict[Any, str]) -> str:
    if len(labels) != 1:
        return ""
    return str(next(iter(labels.values()))).strip()


def _numeric_part(value: object) -> float | str:
    match = re.search(r"\d+(?:\.\d+)?", str(value or ""))
    if not match:
        return ""
    number = float(match.group(0))
    return int(number) if number.is_integer() else number


def _join_unique(values) -> str:
    return ", ".join(
        dict.fromkeys(
            str(value).strip()
            for value in values
            if _has_value(value)
        )
    )


def _first_text(*values: object) -> str:
    for value in values:
        if _has_value(value):
            return str(value).strip()
    return ""


def _has_value(value: object) -> bool:
    if value is None:
        return False
    try:
        if pd.isna(value):
            return False
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    return bool(text and text.lower() not in {"nan", "none"})
