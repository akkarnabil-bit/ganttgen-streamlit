import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

STATUT_COLORS = {
    "terminé": "#2ecc71", "done": "#2ecc71",
    "en cours": "#3498db", "in progress": "#3498db",
    "à faire": "#95a5a6", "todo": "#95a5a6",
    "bloqué": "#e74c3c", "blocked": "#e74c3c",
    "en retard": "#e67e22", "late": "#e67e22",
}


def generate_gantt(df, color_by="Responsable", show_today=True, show_legend=True):
    if color_by not in df.columns:
        color_by = "Responsable"

    df = df.copy()
    df["_label"] = df.apply(lambda r: f"{r['Tâche']} ({r['Avancement']}%)", axis=1)

    color_map = None
    if color_by == "Statut":
        color_map = {val: STATUT_COLORS.get(val.lower().strip(), "#bdc3c7") for val in df["Statut"].unique()}

    fig = px.timeline(
        df,
        x_start="Début", x_end="Fin",
        y="_label",
        color=color_by,
        color_discrete_map=color_map,
        hover_data={"Tâche": True, "Responsable": True, "Statut": True,
                    "Avancement": True, "Début": "|%d/%m/%Y", "Fin": "|%d/%m/%Y", "_label": False},
        labels={"_label": "Tâche"},
    )

    fig.update_yaxes(autorange="reversed")

    for i, row in df.iterrows():
        if row["Avancement"] > 0:
            total_days = (row["Fin"] - row["Début"]).days
            progress_end = row["Début"] + pd.Timedelta(days=total_days * row["Avancement"] / 100)
            fig.add_shape(type="rect", x0=row["Début"], x1=progress_end,
                          y0=i - 0.4, y1=i + 0.4, fillcolor="rgba(0,0,0,0.25)", line_width=0, layer="above")

    if show_today:
        fig.add_vline(x=pd.Timestamp(date.today()), line_width=2, line_dash="dash",
                      line_color="#e74c3c", annotation_text="Aujourd'hui",
                      annotation_position="top right", annotation_font_color="#e74c3c")

    fig.update_layout(
        height=max(420, len(df) * 45 + 100),
        showlegend=show_legend,
        legend_title_text=color_by,
        plot_bgcolor="#fafafa", paper_bgcolor="#ffffff",
        font=dict(family="Inter, Arial, sans-serif", size=13),
        margin=dict(l=20, r=20, t=30, b=40),
        xaxis=dict(gridcolor="#ececec", tickformat="%d %b %Y", tickangle=-30),
        yaxis=dict(tickfont=dict(size=12), gridcolor="#ececec"),
    )

    return fig