from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

import pandas as pd

from src.builder.analytic_db_builder import (
    build_configuracion_dashboard,
)
from src.builder.respondentes_builder import build_respondentes
from src.builder.variables_builder import build_variables
from src.database.db_reader import list_tables, read_table
from src.database.db_writer import write_tables
from src.utils.variable_safety import banner_filter_exclusion_reason


def update_datamap_configuration(
    datamap_df: pd.DataFrame,
    banner_variables: Iterable[str],
    filter_variables: Iterable[str],
) -> pd.DataFrame:
    if datamap_df is None or datamap_df.empty:
        raise ValueError("El Datamap está vacío.")
    if "variable" not in datamap_df.columns:
        raise ValueError("El Datamap no contiene la columna variable.")

    updated = datamap_df.copy()
    variable_names = updated["variable"].fillna("").astype(str)
    available = set(variable_names)
    banners = {str(value) for value in banner_variables}
    filters = {str(value) for value in filter_variables}
    unknown = (banners | filters) - available
    if unknown:
        names = ", ".join(sorted(unknown))
        raise ValueError(
            f"Variables no encontradas en el Datamap: {names}"
        )

    updated["es_banner"] = variable_names.isin(banners)
    updated["es_filtro"] = variable_names.isin(filters)
    return updated


def apply_dashboard_configuration(
    db_path: Path,
    df_spss: pd.DataFrame,
    meta_spss: Any,
    datamap_df: pd.DataFrame,
    banner_variables: Iterable[str],
    filter_variables: Iterable[str],
) -> dict[str, Any]:
    """Atomically replace SQLite after applying banner/filter flags."""
    if not db_path.exists():
        raise FileNotFoundError(
            "Primero debes construir la base analítica."
        )

    safe_banners, skipped_banners = _safe_configuration_variables(
        df_spss, banner_variables
    )
    safe_filters, skipped_filters = _safe_configuration_variables(
        df_spss, filter_variables
    )
    if skipped_banners or skipped_filters:
        skipped = sorted(set(skipped_banners + skipped_filters))
        raise ValueError(
            "Estas variables no se pueden usar como banner/filtro "
            "porque pueden generar una base inestable: "
            + "; ".join(skipped)
        )

    updated_datamap = update_datamap_configuration(
        datamap_df,
        banner_variables=safe_banners,
        filter_variables=safe_filters,
    )
    tables = {
        name: read_table(db_path, name)
        for name in list_tables(db_path)
    }
    old_respondents = tables.get("respondentes", pd.DataFrame())
    old_variables = tables.get("variables", pd.DataFrame())
    old_options = tables.get("opciones", pd.DataFrame())
    old_config = tables.get(
        "configuracion_dashboard", pd.DataFrame()
    )
    respondents = build_respondentes(
        df_spss, updated_datamap
    )
    variables = build_variables(
        df_spss, meta_spss, updated_datamap
    )
    config = build_configuracion_dashboard(
        updated_datamap,
        tables.get("recomendaciones_reporteador"),
        df_spss=df_spss,
    )
    (
        respondents,
        variables,
        config,
        options,
    ) = _preserve_active_factors(
        tables.get("factores_configurados"),
        old_respondents,
        old_variables,
        old_config,
        old_options,
        respondents,
        variables,
        config,
    )
    tables["respondentes"] = respondents
    tables["variables"] = variables
    tables["configuracion_dashboard"] = config
    tables["opciones"] = options

    temp_path = db_path.with_name(
        f".{db_path.stem}.{uuid4().hex}.tmp{db_path.suffix}"
    )
    try:
        write_tables(temp_path, tables)
        _validate_configuration(
            temp_path,
            banner_variables=banner_variables,
            filter_variables=filter_variables,
        )
        temp_path.replace(db_path)
    finally:
        temp_path.unlink(missing_ok=True)

    return {
        "db_path": db_path,
        "datamap": updated_datamap,
        "tables": tables,
    }


def _validate_configuration(
    db_path: Path,
    banner_variables: Iterable[str],
    filter_variables: Iterable[str],
) -> None:
    config = read_table(db_path, "configuracion_dashboard")
    respondents = read_table(db_path, "respondentes")
    variables = read_table(db_path, "variables")

    expected_banners = {str(value) for value in banner_variables}
    expected_filters = {str(value) for value in filter_variables}
    try:
        factors = read_table(db_path, "factores_configurados")
    except Exception:
        factors = pd.DataFrame()
    if not factors.empty:
        active = pd.to_numeric(
            factors["activo"], errors="coerce"
        ).fillna(0).astype(bool)
        expected_banners.update(
            factors.loc[
                active
                & pd.to_numeric(
                    factors["como_banner"], errors="coerce"
                )
                .fillna(0)
                .astype(bool),
                "variable_derivada",
            ]
            .dropna()
            .astype(str)
        )
        expected_filters.update(
            factors.loc[
                active
                & pd.to_numeric(
                    factors["como_filtro"], errors="coerce"
                )
                .fillna(0)
                .astype(bool),
                "variable_derivada",
            ]
            .dropna()
            .astype(str)
        )
    actual_banners = set(
        config.loc[
            config["tipo_configuracion"].eq("banner"), "variable"
        ].astype(str)
    )
    actual_filters = set(
        config.loc[
            config["tipo_configuracion"].eq("filtro"), "variable"
        ].astype(str)
    )
    if actual_banners != expected_banners:
        raise RuntimeError(
            "La validación de banners en SQLite no fue consistente."
        )
    if actual_filters != expected_filters:
        raise RuntimeError(
            "La validación de filtros en SQLite no fue consistente."
        )

    configured = expected_banners | expected_filters
    missing_columns = configured - set(respondents.columns)
    if missing_columns:
        names = ", ".join(sorted(missing_columns))
        raise RuntimeError(
            "Faltan variables configuradas en respondentes: "
            f"{names}"
        )

    by_variable = variables.set_index("variable")
    for variable in expected_banners:
        if not bool(by_variable.at[variable, "es_banner"]):
            raise RuntimeError(
                f"No se guardó es_banner para {variable}."
            )
    for variable in expected_filters:
        if not bool(by_variable.at[variable, "es_filtro"]):
            raise RuntimeError(
                f"No se guardó es_filtro para {variable}."
            )


def _safe_configuration_variables(
    df_spss: pd.DataFrame,
    variables: Iterable[str],
) -> tuple[list[str], list[str]]:
    safe = []
    skipped = []
    for variable in variables:
        name = str(variable or "").strip()
        reason = banner_filter_exclusion_reason(df_spss, name)
        if reason:
            skipped.append(f"{name} ({reason})")
        else:
            safe.append(name)
    return safe, skipped


def _preserve_active_factors(
    factors: pd.DataFrame | None,
    old_respondents: pd.DataFrame,
    old_variables: pd.DataFrame,
    old_config: pd.DataFrame,
    old_options: pd.DataFrame,
    respondents: pd.DataFrame,
    variables: pd.DataFrame,
    config: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    if factors is None or factors.empty:
        return respondents, variables, config, old_options
    active = factors[
        pd.to_numeric(
            factors["activo"], errors="coerce"
        ).fillna(0).astype(bool)
    ]
    derived = (
        active["variable_derivada"]
        .dropna()
        .astype(str)
        .str.strip()
    )
    derived = [value for value in derived if value]
    if not derived:
        decisions = old_config[
            old_config["tipo_configuracion"].isin(
                ["factor_score_activo", "factor_score_inactivo"]
            )
        ]
        return (
            respondents,
            variables,
            pd.concat([config, decisions], ignore_index=True),
            old_options,
        )

    for variable in derived:
        if variable in old_respondents:
            source = old_respondents.set_index("row_index")[
                variable
            ]
            respondents[variable] = respondents["row_index"].map(
                source
            )
    derived_rows = old_variables[
        old_variables["variable"].astype(str).isin(derived)
    ]
    variables = pd.concat(
        [variables, derived_rows], ignore_index=True
    )
    preserved_config = old_config[
        old_config["variable"].astype(str).isin(
            [
                *derived,
                *factors["factor_id"].astype(str).tolist(),
            ]
        )
    ]
    config = pd.concat(
        [config, preserved_config], ignore_index=True
    )
    factor_options = old_options[
        old_options["variable"].astype(str).isin(derived)
    ]
    options = pd.concat(
        [
            old_options[
                ~old_options["variable"].astype(str).isin(derived)
            ],
            factor_options,
        ],
        ignore_index=True,
    )
    return respondents, variables, config, options
