from __future__ import annotations

import pandas as pd


def expand_banner(
    data: pd.DataFrame,
    respondentes: pd.DataFrame,
    opciones: pd.DataFrame,
    banner: str | list[str] | tuple[str, ...] | None,
    mode: str = "nested",
) -> pd.DataFrame:
    if data.empty:
        return data.copy()
    banners = normalize_banners(banner, respondentes)
    if not banners:
        result = data.copy()
        result["banner"] = "Total"
        return result
    banner_mode = normalize_banner_mode(mode)
    if banner_mode == "separate" and len(banners) > 1:
        return _expand_separate_banners(
            data, respondentes, opciones, banners
        )

    lookup_variables = [
        variable
        for variable in banners
        if variable != "id_respondente"
    ]
    temp_names = {
        variable: f"__banner_value_{index}"
        for index, variable in enumerate(lookup_variables)
    }
    lookup = (
        respondentes[["id_respondente", *lookup_variables]]
        .drop_duplicates("id_respondente")
        .rename(columns=temp_names)
    )
    result = data.merge(lookup, on="id_respondente", how="left")
    display_columns = []
    for index, variable in enumerate(banners):
        source = (
            "id_respondente"
            if variable == "id_respondente"
            else temp_names[variable]
        )
        display_column = f"__banner_display_{index}"
        labels = value_label_lookup(opciones, variable)
        result[display_column] = result[source].apply(
            lambda value, label_map=labels: banner_heading(
                value, label_map
            )
        )
        display_columns.append((variable, display_column))

    if len(display_columns) == 1:
        result["banner"] = result[display_columns[0][1]]
    else:
        result["banner"] = result.apply(
            lambda row: " / ".join(
                f"{variable}: {row[column]}"
                for variable, column in display_columns
            ),
            axis=1,
        )
    result = result.drop(
        columns=[
            *temp_names.values(),
            *(column for _, column in display_columns),
        ],
        errors="ignore",
    )

    total = result.copy()
    total["banner"] = "Total"
    return pd.concat([total, result], ignore_index=True)


def _expand_separate_banners(
    data: pd.DataFrame,
    respondentes: pd.DataFrame,
    opciones: pd.DataFrame,
    banners: list[str],
) -> pd.DataFrame:
    total = data.copy()
    total["banner"] = "Total"
    expanded = [total]
    respondent_lookup = respondentes.drop_duplicates("id_respondente")

    for index, variable in enumerate(banners):
        result = data.copy()
        source = "id_respondente"
        temporary = f"__banner_value_{index}"
        if variable != "id_respondente":
            lookup = respondent_lookup[
                ["id_respondente", variable]
            ].rename(columns={variable: temporary})
            result = result.merge(
                lookup, on="id_respondente", how="left"
            )
            source = temporary
        labels = value_label_lookup(opciones, variable)
        result["banner"] = result[source].apply(
            lambda value, label_map=labels, name=variable: (
                f"{name}: {banner_heading(value, label_map)}"
            )
        )
        result = result.drop(columns=[temporary], errors="ignore")
        expanded.append(result)

    return pd.concat(expanded, ignore_index=True)


def normalize_banners(
    banner: str | list[str] | tuple[str, ...] | None,
    respondentes: pd.DataFrame | None = None,
) -> list[str]:
    if not banner:
        return []
    values = [banner] if isinstance(banner, str) else list(banner)
    unique = [
        value
        for value in dict.fromkeys(
            str(item).strip() for item in values if str(item).strip()
        )
    ]
    if respondentes is not None:
        unique = [
            variable
            for variable in unique
            if variable in respondentes.columns
        ]
    return unique


def normalize_banner_mode(mode: object) -> str:
    normalized = str(mode or "").strip().lower().replace("-", " ")
    if normalized in {
        "separate",
        "separado",
        "separados",
        "no anidado",
        "no anidados",
        "non nested",
    }:
        return "separate"
    return "nested"


def banner_comparison_groups(
    values: pd.Series,
    banners: list[str],
    mode: str,
) -> list[list[str]] | None:
    if normalize_banner_mode(mode) != "separate" or len(banners) < 2:
        return None
    categories = [
        item for item in banner_order(values) if item != "Total"
    ]
    groups = [
        [
            category
            for category in categories
            if category.startswith(f"{variable}: ")
        ]
        for variable in banners
    ]
    return [group for group in groups if group]


def value_label_lookup(
    opciones: pd.DataFrame, variable: str
) -> dict[str, str]:
    if opciones is None or opciones.empty:
        return {}
    required = {"variable", "codigo", "label"}
    if not required.issubset(opciones.columns):
        return {}
    selected = opciones[opciones["variable"].astype(str) == str(variable)]
    lookup = {}
    for _, row in selected.iterrows():
        code = code_text(row.get("codigo"))
        label = str(row.get("label", "")).strip()
        if code and label and code not in lookup:
            lookup[code] = label
    return lookup


def banner_heading(value: object, labels: dict[str, str]) -> str:
    code = code_text(value)
    if not code:
        return "Sin dato"
    label = labels.get(code, "")
    return f"{code} | {label}" if label and label != code else code


def banner_order(values: pd.Series) -> list[str]:
    unique = list(
        dict.fromkeys(values.fillna("Sin dato").astype(str).tolist())
    )
    categories = [value for value in unique if value != "Total"]
    if categories and all(
        ": " in value and " / " not in value
        for value in categories
    ):
        prefixes = list(
            dict.fromkeys(value.split(": ", 1)[0] for value in categories)
        )
        categories = [
            value
            for prefix in prefixes
            for value in sorted(
                [
                    item
                    for item in categories
                    if item.startswith(f"{prefix}: ")
                ],
                key=lambda item: _heading_sort_key(
                    item.split(": ", 1)[1]
                ),
            )
        ]
    else:
        categories.sort(key=_heading_sort_key)
    return (["Total"] if "Total" in unique else []) + categories


def code_text(value: object) -> str:
    if pd.isna(value):
        return ""
    try:
        numeric = float(value)
        if numeric.is_integer():
            return str(int(numeric))
    except (TypeError, ValueError):
        pass
    return str(value).strip()


def _heading_sort_key(value: str) -> tuple[int, float | str]:
    code = value.split(" | ", 1)[0]
    try:
        return (0, float(code))
    except ValueError:
        return (1, code.lower())
