from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.builder.recommendations_builder import (
    build_recomendaciones_reporteador,
)
from src.utils.text_utils import find_column, first_existing


EXPORT_COLUMN_NAMES = {
    "variable": "Variable",
    "label": "Variable_Label",
    "pregunta_id": "Pregunta_ID",
    "texto_pregunta": "Texto_Pregunta",
    "tipo_pregunta": "Tipo_Pregunta",
    "clasificacion_analitica": "Rol_Analitico_Principal",
    "usar_en_dashboard": "Usar_En_Dashboard",
    "es_banner": "Es_Banner",
    "es_filtro": "Es_Filtro",
    "es_ponderador": "Es_Ponderador",
    "tipo_calculo": "Tipo_Calculo",
    "regla_transformacion": "Regla_Transformacion",
    "observacion_usuario": "Observacion_Usuario",
    "seccion": "Seccion",
    "numero_pregunta": "Numero_Pregunta",
    "base_valida": "Base_Valida",
    "orden_cuestionario": "Orden_Cuestionario",
    "seccion_cuestionario": "Seccion_Cuestionario",
    "bloque_cuestionario": "Bloque_Cuestionario",
    "grupo_menu_reporteador": "Grupo_Menu_Reporteador",
    "mostrar_en_menu_reporteador": (
        "Mostrar_En_Menu_Reporteador"
    ),
    "prioridad_reporteador": "Prioridad_Reporteador",
    "es_banner_recomendado": "Es_Banner_Recomendado",
    "es_filtro_recomendado": "Es_Filtro_Recomendado",
    "nivel_relevancia_comercial": (
        "Nivel_Relevancia_Comercial"
    ),
    "justificacion_banner_filtro": (
        "Justificacion_Banner_Filtro"
    ),
    "uso_comercial_sugerido": "Uso_Comercial_Sugerido",
    "distribucion_base": "Distribucion_Base",
    "riesgo_uso_analitico": "Riesgo_Uso_Analitico",
    "requiere_factor": "Requiere_Factor",
    "tipo_factor_recomendado": "Tipo_Factor_Recomendado",
    "variables_para_factor": "Variables_Para_Factor",
    "regla_factor_sugerida": "Regla_Factor_Sugerida",
    "justificacion_factor": "Justificacion_Factor",
    "prioridad_factor": "Prioridad_Factor",
}

EXISTING_COLUMN_ALIASES = {
    "variable": ["Variable", "Variable_SPSS"],
    "label": ["Variable_Label", "Label"],
    "clasificacion_analitica": [
        "Rol_Analitico_Principal",
        "Clasificacion_Analitica",
    ],
}


def save_final_datamap(
    path: Path,
    sheets: dict[str, pd.DataFrame],
    review: pd.DataFrame,
    df_spss: pd.DataFrame | None = None,
    meta_spss=None,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    recommendations = build_recomendaciones_reporteador(
        review,
        sheets,
        df_spss=df_spss,
        meta_spss=meta_spss,
    )
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        review_written = False
        for name, frame in sheets.items():
            if name == "08_Clasificacion_Analitica":
                _merge_review_into_source(frame, review).to_excel(
                    writer,
                    sheet_name=name,
                    index=False,
                )
                review_written = True
                continue
            if name == "11_Banners_Filtros_Recomendados":
                frame = _sanitize_banner_recommendations(
                    frame, recommendations
                )
            frame.to_excel(writer, sheet_name=name[:31], index=False)
        if not review_written:
            _export_review(review).to_excel(
                writer,
                sheet_name="08_Clasificacion_Analitica",
                index=False,
            )
        if "10_Datamap_Corregido" not in sheets:
            _export_review(review).to_excel(
                writer,
                sheet_name="10_Datamap_Corregido",
                index=False,
            )
    return path


def _merge_review_into_source(
    source: pd.DataFrame,
    review: pd.DataFrame,
) -> pd.DataFrame:
    if source is None or source.empty:
        return _export_review(review)
    if review is None or review.empty or "variable" not in review:
        return source.copy()

    result = source.copy()
    source_variable = find_column(
        result.columns,
        EXISTING_COLUMN_ALIASES["variable"],
    )
    if not source_variable:
        return _export_review(review)

    review_values = review.copy()
    review_values["_merge_variable"] = (
        review_values["variable"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )
    review_values = review_values.drop_duplicates(
        "_merge_variable", keep="first"
    ).set_index("_merge_variable")
    source_keys = (
        result[source_variable]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
    )

    targets: dict[str, str] = {}
    for canonical, preferred in EXPORT_COLUMN_NAMES.items():
        if canonical not in review:
            continue
        aliases = [
            preferred,
            canonical,
            *EXISTING_COLUMN_ALIASES.get(canonical, []),
        ]
        target = first_existing(result.columns, aliases)
        if not target:
            target = preferred
            result[target] = ""
        targets[canonical] = target
        mapped = source_keys.map(
            review_values[canonical].to_dict()
        )
        found = source_keys.isin(review_values.index)
        result.loc[found, target] = mapped.loc[found]

    existing_keys = set(source_keys)
    missing = review_values[
        ~review_values.index.isin(existing_keys)
    ]
    if not missing.empty:
        additions = pd.DataFrame(
            "", index=range(len(missing)), columns=result.columns
        )
        for position, (_, row) in enumerate(missing.iterrows()):
            for canonical, target in targets.items():
                additions.at[position, target] = row.get(
                    canonical, ""
                )
        result = pd.concat([result, additions], ignore_index=True)
    return result


def _export_review(review: pd.DataFrame) -> pd.DataFrame:
    if review is None:
        return pd.DataFrame()
    result = review.copy()
    return result.rename(
        columns={
            canonical: preferred
            for canonical, preferred in EXPORT_COLUMN_NAMES.items()
            if canonical in result
        }
    )


def _sanitize_banner_recommendations(
    frame: pd.DataFrame,
    recommendations: pd.DataFrame,
) -> pd.DataFrame:
    if frame.empty or recommendations.empty:
        return frame.copy()
    variable_column = first_existing(
        frame.columns, ["Variable", "variable"]
    )
    if not variable_column:
        return frame.copy()
    source = recommendations[
        recommendations["tipo_recomendacion"].astype(str).eq(
            "banner_filtro"
        )
    ].drop_duplicates("variable").set_index("variable")
    result = frame.copy()
    variables = result[variable_column].astype(str)
    result["Justificacion_Banner_Filtro"] = variables.map(
        source["justificacion"]
    ).fillna("")
    result["Distribucion_Base"] = variables.map(
        source["distribucion_base"]
    ).fillna("")
    justification_column = first_existing(
        result.columns, ["Justificacion"]
    )
    if justification_column:
        result[justification_column] = result[
            "Justificacion_Banner_Filtro"
        ]
    base_column = first_existing(
        result.columns, ["Base_Categorias_Obs"]
    )
    if base_column:
        result[base_column] = result["Distribucion_Base"]
    return result
