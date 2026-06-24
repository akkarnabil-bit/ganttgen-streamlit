# core/chart.py
import pandas as pd
import plotly.express as px
from datetime import date

from core.config import (
    STATUT_COLORS, DEFAULT_STATUS_COLOR, COLOR_BY_PRIORITY,
    CHART_FONT_FAMILY, CHART_FONT_SIZE, CHART_BG_PLOT, CHART_BG_PAPER,
    CHART_GRID_COLOR, CHART_ROW_HEIGHT, CHART_MIN_HEIGHT,
    TODAY_LINE_COLOR,
)


def _resolve_color_by(df: pd.DataFrame, requested: str) -> str:
    if requested in df.columns:
        return requested

    available = [c for c in COLOR_BY_PRIORITY if c in df.columns]
    if not available:
        raise ValueError(
            f"Aucune colonne de couleur disponible parmi {COLOR_BY_PRIORITY}."
        )
    return available[0]


def generate_gantt(
    df: pd.DataFrame,
    color_by: str = "Responsable",
    show_today: bool = True,
    show_legend: bool = True,
) -> "plotly.graph_objects.Figure":

    df = df.copy()

    # Fix #1 — safe color column resolution
    color_by = _resolve_color_by(df, color_by)

    # Fix #3 — vectorised label
    df["_label"] = df["Tâche"] + " (" + df["Avancement"].astype(str) + "%)"

    color_map = None
    if color_by == "Statut":
        color_map = {
            val: STATUT_COLORS.get(val.lower().strip(), DEFAULT_STATUS_COLOR)
            for val in df["Statut"].unique()
        }

    fig = px.timeline(
        df,
        x_start="Début",
        x_end="Fin",
        y="_label",
        color=color_by,
        color_discrete_map=color_map,
        hover_data={
            "Tâche": True,
            "Responsable": True,
            "Statut": True,
            "Avancement": True,
            "Début": "|%d/%m/%Y",
            "Fin": "|%d/%m/%Y",
            "_label": False,
        },
        labels={"_label": "Tâche"},
    )

    fig.update_yaxes(autorange="reversed")

    # Progress line overlay
    labels = df["_label"].tolist()
    for i, (_, row) in enumerate(df.iterrows()):
        if row["Avancement"] > 0:
            # Fix #2 — avoid division by zero for same-day tasks
            total_days = max(1, (row["Fin"] - row["Début"]).days)
            progress_point = row["Début"] + pd.Timedelta(
                days=total_days * row["Avancement"] / 100
            )
            fig.add_shape(
                type="line",
                x0=row["Début"],
                x1=progress_point,
                y0=labels[i],
                y1=labels[i],
                yref="y",
                line=dict(color="#f39c12", width=4),
                layer="above",
            )

    if show_today:
        fig.add_vline(
            x=pd.Timestamp(date.today()),
            line_width=2,
            line_dash="dash",
            line_color=TODAY_LINE_COLOR,
            annotation_text="Aujourd'hui",
            annotation_position="top right",
            annotation_font_color=TODAY_LINE_COLOR,
        )

    fig.update_layout(
        height=max(CHART_MIN_HEIGHT, len(df) * CHART_ROW_HEIGHT + 100),
        showlegend=show_legend,
        legend_title_text=color_by,
        plot_bgcolor=CHART_BG_PLOT,
        paper_bgcolor=CHART_BG_PAPER,
        font=dict(family=CHART_FONT_FAMILY, size=CHART_FONT_SIZE),
        margin=dict(l=20, r=20, t=30, b=40),
        xaxis=dict(
            gridcolor=CHART_GRID_COLOR,
            tickformat="%d %b %Y",
            tickangle=-30,
        ),
        yaxis=dict(tickfont=dict(size=12), gridcolor=CHART_GRID_COLOR),
    )

    return fig