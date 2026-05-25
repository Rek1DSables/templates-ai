import streamlit as st
import pandas as pd
import plotly.express as px
from graph import run_analytics
import config

st.set_page_config(
    page_title="Dashboard Analytics",
    page_icon="📈",
    layout="wide",
)

st.title("📈 Dashboard Analytics Automatique")
st.caption(f"LangGraph · Pandas · Plotly · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("⚙️ Configuration")
    uploaded_file = st.file_uploader("Fichier de données *", type=["csv", "xlsx", "xls"])
    period        = st.selectbox("Période d'analyse", config.PERIODS)

    st.markdown("---")
    st.caption(f"**{config.COMPANY_NAME}**")

# ─── Main ─────────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.info("Uploadez un fichier CSV ou Excel dans le panneau gauche pour commencer.", icon="ℹ️")
    st.stop()

if st.button("🚀 Analyser les données", use_container_width=True, type="primary"):
    with st.status("⚙️ Analyse en cours...", expanded=True) as pipeline_status:
        st.write("📂 Chargement des données...")
        st.write("📊 Calcul des statistiques...")
        st.write("🤖 Génération des insights IA...")

        try:
            result = run_analytics(
                file_bytes = uploaded_file.read(),
                file_name  = uploaded_file.name,
                period     = period,
                kpis       = [],
            )

            if result["status"] == "error":
                pipeline_status.update(label="❌ Erreur", state="error")
                for err in result["errors"]:
                    st.error(err)
                st.stop()

            pipeline_status.update(label="✅ Analyse terminée !", state="complete", expanded=False)

            df    = result["df"]
            stats = result["stats"]
            trends = result.get("trends", {})

            # ── Métriques globales ────────────────────────────────────────────
            st.subheader("📊 Vue d'ensemble")
            col1, col2 = st.columns(2)
            col1.metric("📋 Lignes", stats["rows"])
            col2.metric("📊 Colonnes", stats["columns"])

            # Métriques numériques
            numeric = stats.get("numeric", {})
            if numeric:
                cols = st.columns(min(len(numeric), 4))
                for i, (col_name, vals) in enumerate(list(numeric.items())[:4]):
                    trend = trends.get(col_name, {})
                    delta = f"{trend.get('trend_pct', 0):+.1f}%" if trend else None
                    cols[i].metric(
                        col_name[:20],
                        f"{vals['sum']:,.2f}",
                        delta=delta,
                    )

            st.markdown("---")

            # ── Graphiques automatiques ───────────────────────────────────────
            st.subheader("📉 Visualisations")

            numeric_cols = df.select_dtypes(include="number").columns.tolist()
            date_cols    = df.select_dtypes(include=["datetime64"]).columns.tolist()

            if date_cols and numeric_cols:
                date_col = date_cols[0]
                col1, col2 = st.columns(2)

                with col1:
                    fig = px.line(
                        df.sort_values(date_col),
                        x=date_col,
                        y=numeric_cols[0],
                        title=f"Evolution — {numeric_cols[0]}",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    if len(numeric_cols) > 1:
                        fig2 = px.bar(
                            df.sort_values(date_col).tail(20),
                            x=date_col,
                            y=numeric_cols[1],
                            title=f"Distribution — {numeric_cols[1]}",
                        )
                        st.plotly_chart(fig2, use_container_width=True)

            elif len(numeric_cols) >= 2:
                fig = px.scatter(
                    df,
                    x=numeric_cols[0],
                    y=numeric_cols[1],
                    title=f"{numeric_cols[0]} vs {numeric_cols[1]}",
                )
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")

            # ── Aperçu données ────────────────────────────────────────────────
            with st.expander("🗂️ Aperçu des données"):
                st.dataframe(df.head(20), use_container_width=True)

            st.markdown("---")

            # ── Insights IA ───────────────────────────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🤖 Insights IA")
                st.markdown(result.get("insights", "—"))
            with col2:
                st.subheader("💡 Recommandations")
                st.markdown(result.get("recommendations", "—"))

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

st.markdown("---")
st.caption("Template 26 — Dashboard Analytics · [GitHub](https://github.com/Rek1DSables/templates-ai)")