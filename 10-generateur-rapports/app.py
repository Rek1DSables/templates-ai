import streamlit as st
from graph import run_report
import config

st.set_page_config(
    page_title="Générateur de Rapports",
    page_icon="📄",
    layout="centered",
)

st.title("📄 Générateur de Rapports Automatiques")
st.caption(f"LangGraph · Pandas · FPDF · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Uploadez un fichier CSV ou Excel. Le pipeline va :\n"
    "1. Charger et analyser vos données\n"
    "2. Identifier les insights clés\n"
    "3. Générer des recommandations actionnables\n"
    "4. Produire un rapport PDF téléchargeable",
    icon="ℹ️",
)

# ─── Formulaire ──────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Fichier de données *", type=["csv", "xlsx", "xls"])

context = st.text_area(
    "Contexte métier (optionnel)",
    placeholder="Ex : Données de ventes mensuelles par région pour l'année 2024...",
    height=100,
)

submitted = st.button("🚀 Générer le rapport", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not uploaded_file:
        st.error("⚠️ Veuillez uploader un fichier.")
        st.stop()

    with st.status("⚙️ Génération en cours...", expanded=True) as pipeline_status:
        st.write("📂 Chargement du fichier...")
        st.write("📊 Calcul des statistiques...")
        st.write("🤖 Analyse IA en cours...")

        try:
            result = run_report(
                file_bytes = uploaded_file.read(),
                file_name  = uploaded_file.name,
                context    = context,
            )

            final_status = result.get("status", "error")

            if final_status == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result.get("errors", ["Erreur inconnue."]):
                    st.error(err)

            elif final_status == "completed":
                pipeline_status.update(label="✅ Rapport généré !", state="complete", expanded=False)

                df = result.get("df")
                col1, col2, col3 = st.columns(3)
                col1.metric("📋 Lignes", len(df) if df is not None else "—")
                col2.metric("📊 Colonnes", len(df.columns) if df is not None else "—")
                col3.metric("📄 Rapport", "PDF prêt ✓")

                st.markdown("---")

                with st.expander("📊 Analyse & Insights", expanded=True):
                    st.markdown(result.get("interpretation", "—"))

                with st.expander("💡 Recommandations", expanded=True):
                    st.markdown(result.get("recommendations", "—"))

                st.download_button(
                    label="⬇️ Télécharger le rapport PDF",
                    data=result.get("pdf_bytes", b""),
                    file_name=f"rapport_{uploaded_file.name.split('.')[0]}.pdf",
                    mime="application/pdf",
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
st.caption("Template 10 — Générateur de rapports automatiques · [GitHub](https://github.com/Rek1DSables/templates-ai)")