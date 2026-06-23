# app.py
import io

import pandas as pd
import streamlit as st

from core.parser import parse_file, ValidationError
from core.chart import generate_gantt

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="GanttGen",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main-title  { font-size: 2.4rem; font-weight: 700; color: #1f77b4; margin-bottom: 0; }
    .subtitle    { font-size: 1rem; color: #666; margin-top: 0; margin-bottom: 2rem; }
    .info-box    { background: #f0f6ff; border-left: 4px solid #1f77b4;
                   padding: 1rem 1.2rem; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="main-title">📊 GanttGen</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Génère un diagramme de Gantt interactif depuis un fichier Excel ou CSV</p>',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar — options + template download
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("⚙️ Options")
    color_by    = st.selectbox("Colorier par", options=["Responsable", "Statut", "Catégorie"], index=0)
    show_today  = st.toggle("Afficher la ligne Aujourd'hui", value=True)
    show_legend = st.toggle("Afficher la légende", value=True)

    st.divider()
    st.subheader("📥 Format du fichier")
    st.markdown("""
| Colonne | Type |
|---|---|
| `Tâche` | Texte |
| `Début` | Date |
| `Fin` | Date |
| `Responsable` | Texte |
| `Statut` | Texte |
| `Catégorie` | Texte *(optionnel)* |
| `Avancement` | Nombre 0-100 *(optionnel)* |

Formats acceptés : **`.xlsx`** et **`.csv`**
""")
    st.divider()

    template_df = pd.DataFrame({
        "Tâche":       ["Analyse des besoins", "Conception UI", "Développement backend", "Tests", "Déploiement"],
        "Début":       ["2025-01-06", "2025-01-13", "2025-01-20", "2025-02-10", "2025-02-24"],
        "Fin":         ["2025-01-12", "2025-01-24", "2025-02-09", "2025-02-23", "2025-02-28"],
        "Responsable": ["Alice", "Bob", "Alice", "Charlie", "Bob"],
        "Statut":      ["Terminé", "Terminé", "En cours", "À faire", "À faire"],
        "Catégorie":   ["Planification", "Design", "Dev", "QA", "Ops"],
        "Avancement":  [100, 100, 60, 0, 0],
    })

    xlsx_buf = io.BytesIO()
    template_df.to_excel(xlsx_buf, index=False)
    st.download_button(
        label="📄 Télécharger le template Excel",
        data=xlsx_buf.getvalue(),
        file_name="template_gantt.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    csv_bytes = template_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📄 Télécharger le template CSV",
        data=csv_bytes,
        file_name="template_gantt.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------------------------
# Main area — file upload
# ---------------------------------------------------------------------------

col_upload, col_info = st.columns([2, 1])

with col_upload:
    uploaded_file = st.file_uploader(
        "📂 Importer ton fichier (.xlsx ou .csv)",
        type=["xlsx", "csv"],
    )

with col_info:
    st.markdown("""
<div class="info-box">
<b>Comment ça marche ?</b><br>
1. Télécharge le <b>template</b> (barre latérale)<br>
2. Remplis-le avec tes tâches<br>
3. Importe-le ici (.xlsx ou .csv)<br>
4. Ton Gantt s'affiche instantanément 🎉
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Processing
# ---------------------------------------------------------------------------

if uploaded_file is not None:
    try:
        with st.spinner("Lecture du fichier..."):
            df = parse_file(uploaded_file)

        st.success(f"✅ Fichier chargé — **{len(df)} tâches** trouvées")

        tab_gantt, tab_data, tab_stats = st.tabs(
            ["📊 Diagramme de Gantt", "📋 Données", "📈 Statistiques"]
        )

        with tab_gantt:
            with st.spinner("Génération du Gantt..."):
                fig = generate_gantt(
                    df,
                    color_by=color_by,
                    show_today=show_today,
                    show_legend=show_legend,
                )
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("**Exporter le diagramme**")
            exp_col1, exp_col2, exp_col3 = st.columns(3)

            html_bytes = fig.to_html(full_html=True).encode("utf-8")
            exp_col1.download_button(
                "⬇️ HTML",
                data=html_bytes,
                file_name="gantt.html",
                mime="text/html",
            )

            try:
                import kaleido  # noqa: F401
                png_bytes = fig.to_image(format="png", scale=2)
                exp_col2.download_button(
                    "🖼️ PNG",
                    data=png_bytes,
                    file_name="gantt.png",
                    mime="image/png",
                )
            except Exception:
                exp_col2.button(
                    "🖼️ PNG (non disponible)",
                    disabled=True,
                    help="Installe kaleido dans ton environnement local pour activer cet export.",
                )

            try:
                import kaleido  # noqa: F401
                pdf_bytes = fig.to_image(format="pdf")
                exp_col3.download_button(
                    "📄 PDF",
                    data=pdf_bytes,
                    file_name="gantt.pdf",
                    mime="application/pdf",
                )
            except Exception:
                exp_col3.button(
                    "📄 PDF (non disponible)",
                    disabled=True,
                    help="Installe kaleido dans ton environnement local pour activer cet export.",
                )

        with tab_data:
            st.dataframe(
                df,
                use_container_width=True,
                column_config={
                    "Début":      st.column_config.DateColumn("Début", format="DD/MM/YYYY"),
                    "Fin":        st.column_config.DateColumn("Fin",   format="DD/MM/YYYY"),
                    "Avancement": st.column_config.ProgressColumn("Avancement", min_value=0, max_value=100),
                },
            )

        with tab_stats:
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            durations = (df["Fin"] - df["Début"]).dt.days + 1
            col_s1.metric("Total tâches",         len(df))
            col_s2.metric("Durée totale (jours)", int(durations.sum()))
            col_s3.metric("Tâche la plus longue", f"{int(durations.max())}j")
            col_s4.metric("Avancement moyen",     f"{df['Avancement'].mean():.0f}%")

            if "Statut" in df.columns:
                st.subheader("Répartition par statut")
                st.bar_chart(df["Statut"].value_counts())

            if "Responsable" in df.columns:
                st.subheader("Charge par responsable")
                st.bar_chart(
                    df.groupby("Responsable")["Tâche"].count().rename("Nombre de tâches")
                )

    except ValidationError as e:
        st.error(f"❌ Erreur dans le fichier : {e}")
    except Exception as e:
        st.error(f"❌ Erreur inattendue : {e}")

else:
    st.markdown("---")
    st.markdown(
        "<div style='text-align:center; color:#aaa; padding: 3rem;'>"
        "<h3>📂 Importe ton fichier Excel ou CSV pour commencer</h3>"
        "</div>",
        unsafe_allow_html=True,
    )