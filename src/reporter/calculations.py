from __future__ import annotations

import numpy as np
import pandas as pd


def find_weight_column(
    datamap_df: pd.DataFrame, df_spss: pd.DataFrame
) -> str | None:
    if datamap_df is None or datamap_df.empty:
        return None
    weight_rows = datamap_df[
        (datamap_df.get("es_ponderador", False) == True)
        | (
            datamap_df.get("clasificacion_analitica", "").astype(str)
            == "Ponderador"
        )
    ]
    for variable in weight_rows.get("variable", []):
        if variable in df_spss.columns:
            return str(variable)
    return None


def weight_series(
    datamap_df: pd.DataFrame, df_spss: pd.DataFrame
) -> pd.Series:
    column = find_weight_column(datamap_df, df_spss)
    if column:
        return pd.to_numeric(df_spss[column], errors="coerce").fillna(1.0)
    return pd.Series(1.0, index=df_spss.index)


def attach_report_weights(
    data: pd.DataFrame,
    respondentes: pd.DataFrame,
    ponderador: str | None,
) -> pd.DataFrame:
    result = data.copy()
    if ponderador and ponderador in respondentes.columns:
        lookup = respondentes[["id_respondente", ponderador]].rename(
            columns={ponderador: "_peso"}
        )
        result = result.merge(lookup, on="id_respondente", how="left")
        result["_peso"] = pd.to_numeric(
            result["_peso"], errors="coerce"
        ).fillna(1.0)
    else:
        result["_peso"] = 1.0
    return result


def deduplicate_rm(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    return df.drop_duplicates(
        ["id_respondente", "pregunta_id", "codigo_respuesta"]
    )


def remove_exclusive_combinations(
    df: pd.DataFrame, exclusive_labels: list[str]
) -> pd.DataFrame:
    if df.empty or not exclusive_labels:
        return df
    exclusive_norms = [label.lower() for label in exclusive_labels]
    work = df.copy()
    work["_is_exclusive"] = (
        work["respuesta_label"]
        .fillna("")
        .str.lower()
        .apply(lambda text: any(hint in text for hint in exclusive_norms))
    )
    drop_indexes = []
    for _, group in work.groupby(
        ["id_respondente", "pregunta_id"], dropna=False
    ):
        if group["_is_exclusive"].any() and (~group["_is_exclusive"]).any():
            drop_indexes.extend(
                group.loc[group["_is_exclusive"]].index.tolist()
            )
    return (
        work.drop(index=drop_indexes)
        .drop(columns=["_is_exclusive"])
        .reset_index(drop=True)
    )


def top2box(
    value: object,
    scale_min: float | None = None,
    scale_max: float | None = None,
) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0
    if scale_min == 1 and scale_max == 5:
        return int(numeric in (4, 5))
    return int(scale_max is not None and numeric >= scale_max - 1)


def bottom2box(
    value: object,
    scale_min: float | None = None,
    scale_max: float | None = None,
) -> int:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return 0
    if scale_min == 1 and scale_max == 5:
        return int(numeric in (1, 2))
    return int(scale_min is not None and numeric <= scale_min + 1)


def nps_group(value: object) -> str:
    numeric = pd.to_numeric(value, errors="coerce")
    if pd.isna(numeric):
        return ""
    if 0 <= numeric <= 6:
        return "Detractor"
    if numeric in (7, 8):
        return "Pasivo"
    if numeric in (9, 10):
        return "Promotor"
    return ""


def frequency_summary(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    grouped = (
        data.groupby(["banner", "respuesta"], dropna=False)
        .agg(
            n=("id_respondente", "count"),
            n_ponderado=("_peso", "sum"),
            base_respondentes=("id_respondente", "nunique"),
        )
        .reset_index()
    )
    grouped["base"] = grouped.groupby("banner")["n"].transform("sum")
    grouped["porcentaje"] = grouped["n"] / grouped.groupby(
        "banner"
    )["n"].transform("sum")
    grouped["porcentaje_ponderado"] = grouped[
        "n_ponderado"
    ] / grouped.groupby("banner")["n_ponderado"].transform("sum")
    return grouped


def rm_summary(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    bases = data.groupby("banner")["id_respondente"].nunique()
    weighted_bases = data.drop_duplicates(
        ["banner", "id_respondente"]
    ).groupby("banner")["_peso"].sum()
    aggregations = {
        "menciones": ("id_respondente", "count"),
        "respondentes": ("id_respondente", "nunique"),
        "menciones_ponderadas": ("_peso", "sum"),
    }
    if "entidad_loop" in data.columns:
        aggregations["entidad_loop"] = ("entidad_loop", "first")
    if "opcion_rm" in data.columns:
        aggregations["opcion_rm"] = ("opcion_rm", "first")
    if "tipo_estructura" in data.columns:
        aggregations["tipo_estructura"] = ("tipo_estructura", "first")
    result = (
        data.groupby(["banner", "respuesta"], dropna=False)
        .agg(**aggregations)
        .reset_index()
    )
    result["base"] = result["banner"].map(bases)
    result["base_ponderada"] = result["banner"].map(weighted_bases)
    result["pct_respondentes"] = (
        result["respondentes"] / result["base"].replace(0, np.nan)
    ).fillna(0)
    result["pct_menciones"] = result["menciones"] / result.groupby(
        "banner"
    )["menciones"].transform("sum")
    result["base_menciones"] = result.groupby("banner")[
        "menciones"
    ].transform("sum")
    result["pct_respondentes_ponderado"] = (
        result["menciones_ponderadas"]
        / result["base_ponderada"].replace(0, np.nan)
    ).fillna(0)
    result["pct_menciones_ponderado"] = result[
        "menciones_ponderadas"
    ] / result.groupby("banner")["menciones_ponderadas"].transform("sum")
    return result


def scale_summary(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    rows = []
    for banner, group in data.groupby("banner", dropna=False):
        values = pd.to_numeric(group["valor"], errors="coerce")
        valid = group.loc[values.notna()].copy()
        values = pd.to_numeric(valid["valor"], errors="coerce")
        weights = valid["_peso"].fillna(1.0)
        weight_total = weights.sum()
        mean_weighted = (
            float(np.average(values, weights=weights))
            if len(values) and weight_total
            else np.nan
        )
        rows.append(
            {
                "banner": banner,
                "n": valid["id_respondente"].nunique(),
                "media": values.mean(),
                "desviacion_estandar": values.std(ddof=1),
                "media_ponderada": mean_weighted,
                "top2box": valid.get(
                    "top2box", pd.Series(dtype=float)
                ).mean(),
                "bottombox": valid.get(
                    "bottombox", pd.Series(dtype=float)
                ).mean(),
            }
        )
    return pd.DataFrame(rows)


def nps_summary(data: pd.DataFrame) -> pd.DataFrame:
    if data.empty:
        return pd.DataFrame()
    rows = []
    for banner, group in data.groupby("banner", dropna=False):
        valid = group[group["nps_grupo"].isin(
            ["Promotor", "Pasivo", "Detractor"]
        )]
        total = valid["_peso"].sum()
        shares = {
            category: valid.loc[
                valid["nps_grupo"] == category, "_peso"
            ].sum()
            / total
            if total
            else 0.0
            for category in ("Promotor", "Pasivo", "Detractor")
        }
        rows.append(
            {
                "banner": banner,
                "n": valid["id_respondente"].nunique(),
                "promotores": shares["Promotor"],
                "pasivos": shares["Pasivo"],
                "detractores": shares["Detractor"],
                "nps": (shares["Promotor"] - shares["Detractor"]) * 100,
            }
        )
    return pd.DataFrame(rows)
