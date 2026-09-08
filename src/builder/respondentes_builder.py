from __future__ import annotations

import pandas as pd

from src.utils.constants import ID_CANDIDATES, RESPONDENT_CLASSIFICATIONS
from src.utils.text_utils import normalize_text
from src.utils.variable_safety import is_safe_banner_filter_variable


def detect_id_column(df_spss: pd.DataFrame) -> str | None:
    normalized = {normalize_text(col): col for col in df_spss.columns}
    for candidate in ID_CANDIDATES:
        if candidate in normalized:
            return normalized[candidate]
    for norm, original in normalized.items():
        if any(candidate in norm for candidate in ID_CANDIDATES):
            return original
    return None


def build_respondentes(df_spss: pd.DataFrame, datamap_df: pd.DataFrame) -> pd.DataFrame:
    id_col = detect_id_column(df_spss)
    result = pd.DataFrame(index=df_spss.index)
    original_id = _original_id_series(df_spss, id_col)
    result["id_respondente"] = _internal_id_series(df_spss, id_col)
    result["id_original"] = original_id.fillna("").astype(str)
    result["row_index"] = range(len(df_spss))

    if datamap_df is not None and not datamap_df.empty:
        mask = datamap_df["clasificacion_analitica"].isin(RESPONDENT_CLASSIFICATIONS)
        for flag in ("es_banner", "es_filtro", "es_ponderador"):
            if flag in datamap_df.columns:
                mask |= datamap_df[flag].fillna(False).astype(bool)
        extra_cols = []
        for _, row in datamap_df.loc[mask].iterrows():
            col = str(row.get("variable") or "").strip()
            if col not in df_spss:
                continue
            is_weight = bool(row.get("es_ponderador", False))
            if is_weight or is_safe_banner_filter_variable(df_spss, col):
                extra_cols.append(col)
        for col in dict.fromkeys(extra_cols):
            if col not in result.columns:
                result[col] = df_spss[col]
    return result.reset_index(drop=True)


def _original_id_series(
    df_spss: pd.DataFrame, id_col: str | None
) -> pd.Series:
    if id_col and id_col in df_spss:
        return df_spss[id_col]
    return pd.Series(range(1, len(df_spss) + 1), index=df_spss.index)


def _internal_id_series(
    df_spss: pd.DataFrame, id_col: str | None
) -> pd.Series:
    if id_col and id_col in df_spss:
        candidate = df_spss[id_col].astype(str).str.strip()
        invalid = candidate.str.casefold().isin(
            {"", "nan", "none", "null"}
        )
        if not invalid.any() and candidate.is_unique:
            return candidate
    return pd.Series(
        [f"R{index + 1:06d}" for index in range(len(df_spss))],
        index=df_spss.index,
    )
