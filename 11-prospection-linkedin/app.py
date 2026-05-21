import streamlit as st
from graph import run_prospection
import config

st.set_page_config(
    page_title="Prospection LinkedIn",
    page_icon="🎯",
    layout="centered",
)

st.title("🎯 Prospection LinkedIn Automatisée")
st.caption(f"LangGraph · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Renseignez les profils à prospecter. Le pipeline va :\n"
    "1. Scorer chaque profil selon votre offre\n"
    "2. Rédiger un message personnalisé pour les meilleurs profils (score ≥ 6/10)",
    icon="ℹ️",
)

# ─── Formulaire expéditeur & offre ───────────────────────────────────────────
with st.form("prospection_form"):
    st.subheader("👤 Expéditeur")
    col1, col2 = st.columns(2)
    with col1:
        sender_name    = st.text_input("Votre nom *", placeholder="Jean Dupont")
    with col2:
        sender_company = st.text_input("Votre entreprise *", placeholder="Dupont AI")

    st.subheader("🎯 Offre")
    offer_context = st.text_area(
        "Décrivez votre offre / service *",
        placeholder="Ex : Nous automatisons les processus métier des PME via des agents IA sur mesure...",
        height=100,
    )

    st.subheader("👥 Profils à prospecter")
    st.caption("Ajoutez jusqu'à 5 profils manuellement.")

    profiles = []
    for i in range(1, 6):
        with st.expander(f"Profil {i}", expanded=(i == 1)):
            col1, col2 = st.columns(2)
            with col1:
                name    = st.text_input("Nom complet", key=f"name_{i}", placeholder="Marie Martin")
                company = st.text_input("Entreprise",  key=f"company_{i}", placeholder="Martin & Co")
            with col2:
                position = st.text_input("Poste",      key=f"position_{i}", placeholder="Directrice RH")
            summary  = st.text_area("Résumé / Bio LinkedIn", key=f"summary_{i}", height=80,
                                    placeholder="Ex : 10 ans d'expérience en RH, spécialisée dans la transformation digitale...")

            if name.strip():
                profiles.append({
                    "name":     name,
                    "company":  company,
                    "position": position,
                    "summary":  summary,
                })

    submitted = st.form_submit_button("🚀 Lancer la prospection", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not profiles or not offer_context or not sender_name or not sender_company:
        st.error("⚠️ Renseignez au moins un profil et tous les champs obligatoires.")
        st.stop()

    with st.status("⚙️ Prospection en cours...", expanded=True) as pipeline_status:
        st.write(f"🤖 Scoring de {len(profiles)} profil(s)...")
        st.write("✉️ Rédaction des messages en cours...")

        try:
            result = run_prospection(
                profiles       = profiles,
                offer_context  = offer_context,
                sender_name    = sender_name,
                sender_company = sender_company,
            )

            final_status = result.get("status", "error")

            if final_status == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result.get("errors", ["Erreur inconnue."]):
                    st.error(err)

            elif final_status == "completed":
                messages = result.get("messages", [])
                scored   = result.get("scored_profiles", [])

                pipeline_status.update(label="✅ Prospection terminée !", state="complete", expanded=False)

                col1, col2, col3 = st.columns(3)
                col1.metric("👥 Profils analysés", len(scored))
                col2.metric("⭐ Profils retenus", len(messages))
                col3.metric("✉️ Messages rédigés", len(messages))

                st.markdown("---")

                st.subheader("📊 Scoring des profils")
                for p in scored:
                    color = "🟢" if p["score"] >= 7 else "🟡" if p["score"] >= 5 else "🔴"
                    st.markdown(
                        f"{color} **{p['name']}** — {p['company']} | "
                        f"Score : **{p['score']}/10** | {p['priorite']} | _{p['raison']}_"
                    )

                st.markdown("---")

                if messages:
                    st.subheader("✉️ Messages personnalisés")
                    for msg in messages:
                        with st.expander(f"📨 {msg['name']} — {msg['company']} (Score : {msg['score']}/10)"):
                            st.text_area("Message", value=msg["message"], height=150, key=f"msg_{msg['name']}")
                else:
                    st.warning("Aucun profil n'a atteint le score minimum (6/10).")

            else:
                pipeline_status.update(label=f"⚠️ Arrêt à l'étape : {final_status}", state="error")
                for err in result.get("errors", []):
                    st.error(err)

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 11 — Prospection LinkedIn · [GitHub](https://github.com/Rek1DSables/templates-ai)")