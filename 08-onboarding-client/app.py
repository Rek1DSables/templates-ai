import streamlit as st
from graph import run_onboarding
import config

st.set_page_config(
    page_title=f"Onboarding Client — {config.COMPANY_NAME}",
    page_icon="🚀",
    layout="centered",
)

st.title("🚀 Pipeline d'Onboarding Client")
st.caption(f"**{config.COMPANY_NAME}** · LangGraph + Gmail + Supabase")
st.markdown("---")

st.info(
    "Renseignez les informations du nouveau client. Le pipeline va :\n"
    "1. Créer son dossier dans Supabase\n"
    "2. Lui envoyer un email de bienvenue personnalisé\n"
    "3. Lui envoyer un questionnaire de démarrage adapté à son secteur",
    icon="ℹ️",
)

# ─── Formulaire ──────────────────────────────────────────────────────────────
with st.form("onboarding_form"):
    st.subheader("📋 Informations client")

    col1, col2 = st.columns(2)
    with col1:
        name    = st.text_input("Nom complet *", placeholder="Marie Dupont")
        company = st.text_input("Entreprise", placeholder="Dupont & Associés")
    with col2:
        email  = st.text_input("Email *", placeholder="marie@dupont.fr")
        sector = st.selectbox("Secteur d'activité", config.SECTORS)

    project_description = st.text_area(
        "Description du projet *",
        placeholder="Décrivez brièvement le projet ou le besoin du client...",
        height=130,
    )

    submitted = st.form_submit_button("🚀 Lancer l'onboarding", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not name or not email or not project_description:
        st.error("⚠️ Les champs marqués * sont obligatoires.")
        st.stop()

    with st.status("⚙️ Onboarding en cours...", expanded=True) as pipeline_status:
        st.write("🔍 Validation des données...")
        try:
            result = run_onboarding({
                "name":                name,
                "email":               email,
                "company":             company,
                "sector":              sector,
                "project_description": project_description,
            })

            final_status = result.get("status", "error")

            if final_status == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result.get("errors", ["Erreur inconnue."]):
                    st.error(err)

            elif final_status == "completed":
                pipeline_status.update(label="✅ Onboarding terminé !", state="complete", expanded=False)
                st.success(f"✅ **{name}** a été onboardé avec succès.")

                col1, col2, col3 = st.columns(3)
                col1.metric("📁 Supabase", "Créé ✓")
                col2.metric("📧 Bienvenue", "Envoyé ✓")
                col3.metric("📝 Questionnaire", "Envoyé ✓")

                if result.get("client_id"):
                    st.caption(f"ID Supabase : `{result['client_id']}`")

                with st.expander("📧 Email de bienvenue généré"):
                    st.text(result.get("welcome_email_content", "—"))

                with st.expander("📝 Questionnaire généré"):
                    st.text(result.get("questionnaire_content", "—"))

            else:
                pipeline_status.update(label=f"⚠️ Arrêt à l'étape : {final_status}", state="error")
                for err in result.get("errors", []):
                    st.error(err)

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 08 — Onboarding client automatisé · [GitHub](https://github.com/Rek1DSables/templates-ai)")