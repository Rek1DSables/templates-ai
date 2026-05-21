import streamlit as st
from graph import run_analysis
import config

st.set_page_config(
    page_title="Analyse Sentiment & Reviews",
    page_icon="📊",
    layout="centered",
)

st.title("📊 Analyse Sentiment & Reviews")
st.caption(f"LangGraph · Apify · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Entrez l'URL d'une page Google Maps ou Trustpilot. Le pipeline va :\n"
    "1. Récupérer les reviews via Apify\n"
    "2. Analyser le sentiment global\n"
    "3. Identifier les thèmes récurrents\n"
    "4. Générer un rapport de synthèse",
    icon="ℹ️",
)

# ─── Formulaire ──────────────────────────────────────────────────────────────
with st.form("sentiment_form"):
    source = st.selectbox("Source", config.SOURCES)
    url    = st.text_input(
        "URL de la page *",
        placeholder="https://www.google.com/maps/place/...",
    )
    submitted = st.form_submit_button("🚀 Lancer l'analyse", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not url:
        st.error("⚠️ L'URL est obligatoire.")
        st.stop()

    with st.status("⚙️ Analyse en cours...", expanded=True) as pipeline_status:
        st.write("🔍 Validation de l'URL...")
        st.write("📥 Récupération des reviews via Apify...")

        try:
            result = run_analysis(source=source, url=url)
            final_status = result.get("status", "error")

            if final_status == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result.get("errors", ["Erreur inconnue."]):
                    st.error(err)

            elif final_status == "completed":
                pipeline_status.update(label="✅ Analyse terminée !", state="complete", expanded=False)

                # Métriques
                nb_reviews = len(result.get("raw_reviews") or [])
                col1, col2, col3 = st.columns(3)
                col1.metric("📝 Reviews analysées", nb_reviews)
                col2.metric("🔍 Thèmes identifiés", "5")
                col3.metric("📄 Rapport", "Généré ✓")

                st.markdown("---")

                # Résultats
                with st.expander("📊 Analyse sentiment", expanded=True):
                    st.markdown(result.get("sentiment_analysis", "—"))

                with st.expander("🏷️ Thèmes récurrents", expanded=True):
                    st.markdown(result.get("themes", "—"))

                with st.expander("📄 Rapport de synthèse", expanded=True):
                    st.markdown(result.get("report", "—"))

                # Export rapport
                st.download_button(
                    label="⬇️ Télécharger le rapport",
                    data=result.get("report", ""),
                    file_name="rapport_sentiment.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            else:
                pipeline_status.update(label=f"⚠️ Arrêt à l'étape : {final_status}", state="error")
                for err in result.get("errors", []):
                    st.error(err)

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 09 — Analyse sentiment & reviews · [GitHub](https://github.com/Rek1DSables/templates-ai)")