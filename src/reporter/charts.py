from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PALETTE = [
    "#176B87",
    "#D1495B",
    "#EDA33B",
    "#2E8B57",
    "#665191",
    "#4C78A8",
    "#B279A2",
]


def build_chart(
    calculation: str,
    summary: pd.DataFrame,
    title: str,
    has_banner: bool,
    selected_calculations: list[str] | None = None,
) -> go.Figure | None:
    if summary is None or summary.empty:
        return None
    kind = (calculation or "Frecuencia").lower()
    if "nps" in kind:
        figure = _nps_chart(summary, has_banner)
    elif any(token in kind for token in ("media", "top", "bottom")):
        figure = _scale_chart(summary, kind, has_banner)
    elif "rm" in kind:
        value_column = (
            "pct_respondentes_ponderado"
            if selected_calculations
            and "% ponderado" in selected_calculations
            and "pct_respondentes_ponderado" in summary.columns
            else "pct_respondentes"
        )
        figure = _response_chart(
            summary,
            value_column,
            has_banner,
            horizontal=True,
        )
    else:
        value_column = (
            "porcentaje_ponderado"
            if selected_calculations
            and "% ponderado" in selected_calculations
            and "porcentaje_ponderado" in summary.columns
            else "porcentaje"
        )
        figure = _response_chart(
            summary,
            value_column,
            has_banner,
            horizontal=summary["respuesta"].nunique() > 5,
        )
    if figure is None:
        return None
    figure.update_layout(
        title={"text": title, "x": 0, "font": {"size": 16}},
        template="plotly_white",
        colorway=PALETTE,
        margin={"l": 20, "r": 20, "t": 54, "b": 24},
        legend_title_text="",
        hoverlabel={"namelength": -1},
    )
    return figure


def _response_chart(
    summary: pd.DataFrame,
    value_column: str,
    has_banner: bool,
    horizontal: bool,
) -> go.Figure:
    data = _chart_scope(summary, has_banner).copy()
    data["porcentaje_grafico"] = data[value_column] * 100
    banner_order = _banner_order(data, has_banner)
    if horizontal:
        response_order = _response_order_by_total(
            data, "porcentaje_grafico"
        )
        data = data.sort_values("porcentaje_grafico")
        figure = px.bar(
            data,
            x="porcentaje_grafico",
            y="respuesta",
            color="banner" if has_banner else None,
            text="porcentaje_grafico",
            orientation="h",
            barmode="group",
            labels={
                "porcentaje_grafico": "%",
                "respuesta": "",
                "banner": "",
            },
            color_discrete_sequence=PALETTE,
            category_orders={"banner": banner_order},
        )
        figure.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        if has_banner and any(
            str(trace.name) == "Total"
            for trace in figure.data
        ):
            traces = {
                str(trace.name): trace
                for trace in figure.data
            }
            figure.data = tuple(
                traces[name]
                for name in banner_order
                if name in traces
            )
            figure.update_layout(
                legend={"traceorder": "normal"}
            )
        figure.update_xaxes(ticksuffix="%", rangemode="tozero")
        figure.update_yaxes(
            categoryorder="array",
            # En un eje Y, Plotly coloca el primer elemento abajo.
            # Invertimos para que el mayor Total aparezca arriba.
            categoryarray=list(reversed(response_order)),
        )
    else:
        figure = px.bar(
            data,
            x="respuesta",
            y="porcentaje_grafico",
            color="banner" if has_banner else None,
            text="porcentaje_grafico",
            barmode="group",
            labels={
                "porcentaje_grafico": "%",
                "respuesta": "",
                "banner": "",
            },
            color_discrete_sequence=PALETTE,
            category_orders={"banner": banner_order},
        )
        figure.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
        )
        figure.update_yaxes(
            ticksuffix="%",
            range=[0, _percentage_axis_max(data)],
        )
        figure.update_xaxes(tickangle=-20)
    return figure


def _scale_chart(
    summary: pd.DataFrame, kind: str, has_banner: bool
) -> go.Figure:
    data = _chart_scope(summary, has_banner).copy()
    if "top" in kind:
        metric, label, suffix = "top2box", "Top 2 Box", "%"
        data[metric] = data[metric] * 100
    elif "bottom" in kind:
        metric, label, suffix = "bottombox", "Bottom Box", "%"
        data[metric] = data[metric] * 100
    else:
        metric, label, suffix = "media_ponderada", "Media", ""
    figure = px.bar(
        data,
        x="banner",
        y=metric,
        color="banner",
        text=metric,
        labels={"banner": "", metric: label},
        color_discrete_sequence=PALETTE,
    )
    figure.update_traces(
        texttemplate=(
            "%{text:.1f}%" if suffix == "%" else "%{text:.2f}"
        ),
        textposition="outside",
        cliponaxis=False,
    )
    figure.update_yaxes(ticksuffix=suffix, rangemode="tozero")
    figure.update_layout(showlegend=False)
    return figure


def _nps_chart(
    summary: pd.DataFrame, has_banner: bool
) -> go.Figure:
    data = _chart_scope(summary, has_banner).copy()
    figure = go.Figure()
    for metric, label, color in [
        ("promotores", "Promotores", "#2E8B57"),
        ("pasivos", "Pasivos", "#EDA33B"),
        ("detractores", "Detractores", "#D1495B"),
    ]:
        figure.add_bar(
            name=label,
            x=data["banner"],
            y=data[metric] * 100,
            text=data[metric] * 100,
            texttemplate="%{text:.1f}%",
            textposition="inside",
            marker_color=color,
            hovertemplate=f"{label}: %{{y:.1f}}%<extra></extra>",
        )
    figure.update_layout(barmode="stack")
    figure.update_yaxes(title="Distribución", ticksuffix="%")
    return figure


def _chart_scope(
    summary: pd.DataFrame, has_banner: bool
) -> pd.DataFrame:
    if has_banner:
        return summary.copy()
    return summary[summary["banner"] == "Total"].copy()


def _response_order_by_total(
    data: pd.DataFrame, value_column: str
) -> list[str]:
    total = data[
        data["banner"].astype(str).eq("Total")
    ][["respuesta", value_column]]
    if total.empty:
        total = (
            data.groupby("respuesta", sort=False)[value_column]
            .max()
            .reset_index()
        )
    return (
        total.drop_duplicates("respuesta")
        .sort_values(
            value_column,
            ascending=False,
            kind="stable",
        )["respuesta"]
        .astype(str)
        .tolist()
    )


def _banner_order(
    data: pd.DataFrame, has_banner: bool
) -> list[str]:
    if not has_banner:
        return []
    values = list(
        dict.fromkeys(data["banner"].dropna().astype(str))
    )
    return [
        *(["Total"] if "Total" in values else []),
        *[value for value in values if value != "Total"],
    ]


def _percentage_axis_max(data: pd.DataFrame) -> float:
    maximum = pd.to_numeric(
        data["porcentaje_grafico"], errors="coerce"
    ).max()
    if pd.isna(maximum):
        return 100
    return max(100, min(120, float(maximum) * 1.12))
