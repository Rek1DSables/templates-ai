import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import io
from graph import run_prediction
import config

st.set_page_config(
    page_title="Agent de Prédiction",
    page_icon="🔮",
    layout="wide",
)

st.title("🔮 Agent de Prédiction — Time Series")
st.caption(f"LangGraph · NumPy · Pandas · Plotly · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("⚙️ Configuration")

    uploaded_file = st.file_uploader("Fichier de données *", type=["csv", "xlsx", "xls"])

    if uploaded_file:
        try:
            df_preview = pd.read_csv(io.BytesIO(uploaded_file.read())) if uploaded_file.name.endswith(".csv") \
                else pd.read_excel(io.BytesIO(uploaded_file.read()))
            uploaded_file.seek(0)
            columns = df_preview.columns.tolist()

            date_col   = st.selectbox("Colonne date *", columns)
            target_col = st.selectbox("Colonne à prédire *", [c for c in columns if c != date_col])
        except:
            columns    = []
            date_col   = ""
            target_col = ""
    else:
        date_col   = ""
        target_col = ""

    model_type       = st.selectbox("Modèle de prédiction", config.MODELS)
    forecast_periods = st.slider("Périodes à prédire", min_value=7, max_value=90, value=config.FORECAST_PERIODS)

# ─── Main ─────────────────────────────────────────────────────────────────────
if not uploaded_file:
    st.info("Uploadez un fichier CSV ou Excel dans le panneau gauche pour commencer.", icon="ℹ️")
    st.stop()

if st.button("🚀 Lancer la prédiction", use_container_width=True, type="primary"):
    if not date_col or not target_col:
        st.error("⚠️ Sélectionnez les colonnes date et cible.")
        st.stop()

    with st.status("⚙️ Prédiction en cours...", expanded=True) as pipeline_status:
        st.write("📂 Chargement des données...")
        st.write("🔮 Calcul de la prédiction...")
        st.write("🤖 Interprétation IA...")

        try:
            result = run_prediction(
                file_bytes       = uploaded_file.read(),
                file_name        = uploaded_file.name,
                target_col       = target_col,
                date_col         = date_col,
                model_type       = model_type,
                forecast_periods = forecast_periods,
            )

            if result["status"] == "error":
                pipeline_status.update(label="❌ Erreur", state="error")
                for err in result["errors"]:
                    st.error(err)
                st.stop()

            pipeline_status.update(label="✅ Prédiction terminée !", state="complete", expanded=False)

            df       = result["df"]
            df_f     = result["df_forecast"]
            metrics  = result["metrics"]

            # ── Métriques ─────────────────────────────────────────────────────
            st.subheader("📊 Métriques du modèle")
            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric("📉 MAE",           metrics["mae"])
            col2.metric("📉 RMSE",          metrics["rmse"])
            col3.metric("📉 MAPE",          f"{metrics['mape']}%")
            col4.metric("📈 Tendance",      metrics["trend"])
            col5.metric("🔮 Valeur finale", metrics["forecast_end"])

            st.markdown("---")

            # ── Graphique ─────────────────────────────────────────────────────
            st.subheader("📉 Prédiction vs Historique")
            fig = go.Figure()

            # Historique
            fig.add_trace(go.Scatter(
                x=df[date_col], y=df[target_col],
                name="Historique",
                line=dict(color="blue"),
            ))

            # Prédiction
            fig.add_trace(go.Scatter(
                x=df_f["date"], y=df_f["forecast"],
                name="Prédiction",
                line=dict(color="red", dash="dash"),
            ))

            # Intervalle de confiance
            fig.add_trace(go.Scatter(
                x=pd.concat([df_f["date"], df_f["date"][::-1]]),
                y=pd.concat([df_f["upper"], df_f["lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(255,0,0,0.1)",
                line=dict(color="rgba(255,255,255,0)"),
                name="IC 95%",
            ))

            fig.update_layout(
                title=f"Prédiction — {target_col} ({model_type})",
                xaxis_title="Date",
                yaxis_title=target_col,
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True)

            # ── Table prédictions ─────────────────────────────────────────────
            with st.expander("📋 Données de prédiction"):
                st.dataframe(df_f, use_container_width=True)

            st.markdown("---")

            # ── IA ────────────────────────────────────────────────────────────
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🤖 Interprétation IA")
                st.markdown(result.get("interpretation", "—"))
            with col2:
                st.subheader("💡 Recommandations")
                st.markdown(result.get("recommendations", "—"))

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

st.markdown("---")
st.caption("Template 27 — Agent de prédiction · [GitHub](https://github.com/Rek1DSables/templates-ai)")