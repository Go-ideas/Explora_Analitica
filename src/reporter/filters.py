from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.database.db_reader import read_table
from src.reporter.recommendations import configuration_entries


@dataclass(frozen=True)
class FilterChoice:
    value: object
    display: str


def config_entries(
    db_path: Path,
    kind: str,
    datamap_paths=None,
) -> pd.DataFrame:
    if kind in {"banner", "filtro"}:
        return configuration_entries(
            db_path, kind, datamap_paths
        )
    try:
        config = read_table(db_path, "configuracion_dashboard")
    except Exception:
        return pd.DataFrame(
            columns=[
                "tipo_configuracion",
                "variable",
                "pregunta_id",
                "label",
            ]
        )
    if config.empty:
        return config
    selected = config[
        config["tipo_configuracion"] == kind
    ].copy()
    return selected.drop_duplicates("variable").reset_index(
        drop=True
    )


def configured_variables(db_path: Path, kind: str) -> list[str]:
    try:
        config = read_table(db_path, "configuracion_dashboard")
    except Exception:
        return []
    if config.empty:
        return []
    return (
        config.loc[
            config["tipo_configuracion"].eq(kind), "variable"
        ]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .tolist()
    )


def filter_choices(db_path: Path, variable: str) -> list[FilterChoice]:
    try:
        respondentes = read_table(db_path, "respondentes")
        opciones = read_table(db_path, "opciones")
    except Exception:
        return []
    if variable not in respondentes.columns:
        return []

    labels = {}
    if not opciones.empty:
        selected = opciones[opciones["variable"].astype(str) == str(variable)]
        for _, row in selected.iterrows():
            labels[_code_text(row.get("codigo"))] = str(
                row.get("label", "")
            ).strip()

    values = get_available_filter_values(respondentes, variable)
    choices = []
    for value in values:
        code = _code_text(value)
        if not code:
            choices.append(FilterChoice(value=value, display="Sin dato"))
            continue
        label = labels.get(code, "")
        display = f"{code} | {label}" if label and label != code else code
        choices.append(FilterChoice(value=value, display=display))
    return choices


def get_available_filter_values(
    df: pd.DataFrame, filter_variable: str
) -> list[object]:
    if df is None or filter_variable not in df.columns:
        return []
    values = df[filter_variable].drop_duplicates().tolist()
    values.sort(key=_sort_key)
    return values


def apply_multiple_filters(
    df: pd.DataFrame,
    filters_dict: dict[str, list[object]] | None,
) -> pd.DataFrame:
    result = df.copy()
    for variable, values in (filters_dict or {}).items():
        if variable not in result.columns or not values:
            continue
        include_missing = any(pd.isna(value) for value in values)
        non_missing = [value for value in values if not pd.isna(value)]
        mask = pd.Series(False, index=result.index)
        if non_missing:
            numeric_values = pd.to_numeric(
                pd.Series(non_missing), errors="coerce"
            )
            numeric_series = pd.to_numeric(
                result[variable], errors="coerce"
            )
            if numeric_values.notna().all():
                mask |= numeric_series.isin(numeric_values.tolist())
            else:
                normalized = {str(value).strip() for value in non_missing}
                mask |= (
                    result[variable]
                    .fillna("")
                    .astype(str)
                    .str.strip()
                    .isin(normalized)
                )
        if include_missing:
            mask |= result[variable].isna()
        result = result.loc[mask].copy()
    return result


def summarize_filters(
    filters_dict: dict[str, list[object]] | None,
    labels_dict: dict[str, dict[str, str] | list[str]] | None = None,
) -> str:
    parts = []
    labels_dict = labels_dict or {}
    for variable, values in (filters_dict or {}).items():
        if not values:
            continue
        variable_labels = labels_dict.get(variable, {})
        displays = []
        for index, value in enumerate(values):
            if isinstance(variable_labels, dict):
                displays.append(
                    variable_labels.get(_code_text(value), _code_text(value))
                )
            elif index < len(variable_labels):
                displays.append(str(variable_labels[index]))
            else:
                displays.append(_code_text(value))
        parts.append(f"{variable}: {', '.join(displays)}")
    return " | ".join(parts) if parts else "Sin filtros"


def apply_filter(
    respondentes: pd.DataFrame,
    variable: str | None,
    value: object | None,
) -> pd.DataFrame:
    if not variable or value is None:
        return respondentes.copy()
    return apply_multiple_filters(respondentes, {variable: [value]})


def _code_text(value: object) -> str:
    if pd.isna(value):
        return ""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _sort_key(value: object) -> tuple[int, float | str]:
    if pd.isna(value):
        return (2, "")
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, str(value).lower())
