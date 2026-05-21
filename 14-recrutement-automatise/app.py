import streamlit as st
from graph import run_action
import config

st.set_page_config(
    page_title="Recrutement Automatisé",
    page_icon="🎯",
    layout="wide",
)

st.title("🎯 Recrutement Automatisé")
st.caption(f"LangGraph · Supabase · PyMuPDF · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Pipeline", "📄 Analyser un CV", "✏️ Mettre à jour"])

# ─── Tab 1 : Pipeline ─────────────────────────────────────────────────────────
with tab1:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh_pipeline"] = True

    if st.session_state.get("refresh_pipeline", True):
        with st.spinner("Chargement du pipeline..."):
            result = run_action("get_pipeline")

            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                candidates = result.get("candidates", [])
                summary    = result.get("pipeline_summary", "")

                if candidates:
                    # Métriques
                    statuses = [c["status"] for c in candidates]
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("👥 Total",          len(candidates))
                    col2.metric("🆕 Nouveaux",       statuses.count("Nouveau"))
                    col3.metric("⭐ Présélectionnés", statuses.count("Présélectionné"))
                    col4.metric("🤝 Entretiens",     statuses.count("Entretien"))
                    col5.metric("✅ Embauchés",      statuses.count("Embauché"))

                    st.markdown("---")

                    with st.expander("🤖 Résumé IA du pipeline", expanded=True):
                        st.markdown(summary)

                    st.markdown("---")

                    st.subheader("👥 Candidats")
                    for c in candidates:
                        status_icon = {
                            "Nouveau": "🆕", "Présélectionné": "⭐",
                            "Entretien": "🤝", "Offre envoyée": "📨",
                            "Refusé": "❌", "Embauché": "✅"
                        }.get(c["status"], "🆕")

                        with st.expander(f"{status_icon} **{c['name']}** — {c['status']} | `ID : {c['id'][:8]}...`"):
                            st.markdown(c.get("analysis", "Pas d'analyse disponible."))
                else:
                    st.info("Aucun candidat dans le pipeline. Analysez un CV dans l'onglet 📄")

        st.session_state["refresh_pipeline"] = False

# ─── Tab 2 : Analyser un CV ───────────────────────────────────────────────────
with tab2:
    with st.form("analyze_cv_form"):
        st.subheader("📄 Analyser un nouveau CV")

        uploaded_cv = st.file_uploader("CV du candidat (PDF) *", type=["pdf"])
        job_description = st.text_area(
            "Fiche de poste *",
            height=150,
            placeholder="Décrivez le poste, les compétences requises, l'expérience souhaitée...",
        )

        submitted = st.form_submit_button("🚀 Analyser le CV", use_container_width=True, type="primary")

    if submitted:
        if not uploaded_cv or not job_description:
            st.error("⚠️ Le CV et la fiche de poste sont obligatoires.")
        else:
            with st.status("⚙️ Analyse en cours...", expanded=True) as pipeline_status:
                st.write("📄 Extraction du texte...")
                st.write("🤖 Analyse IA en cours...")

                result = run_action(
                    "analyze_cv",
                    cv_bytes        = uploaded_cv.read(),
                    cv_name         = uploaded_cv.name,
                    job_description = job_description,
                )

                if result["status_pipeline"] == "error":
                    pipeline_status.update(label="❌ Erreur", state="error")
                    for err in result["errors"]:
                        st.error(err)
                else:
                    pipeline_status.update(label="✅ Analyse terminée !", state="complete", expanded=False)
                    data = result.get("candidate_data", {})
                    st.success(f"✅ **{data.get('name', 'Candidat')}** analysé et ajouté au pipeline.")

                    with st.expander("📊 Résultat de l'analyse", expanded=True):
                        st.markdown(data.get("analysis", "—"))

                    st.caption(f"ID Supabase : `{data.get('id', '—')}`")
                    st.session_state["refresh_pipeline"] = True

# ─── Tab 3 : Mettre à jour ────────────────────────────────────────────────────
with tab3:
    st.subheader("✏️ Mettre à jour le statut d'un candidat")

    with st.form("update_status_form"):
        candidate_id = st.text_input("ID du candidat *", placeholder="Copiez l'ID depuis le pipeline")
        new_status   = st.selectbox("Nouveau statut *", config.CANDIDATE_STATUSES)

        submitted = st.form_submit_button("✏️ Mettre à jour", use_container_width=True, type="primary")

    if submitted:
        if not candidate_id:
            st.error("⚠️ L'ID du candidat est obligatoire.")
        else:
            with st.spinner("Mise à jour..."):
                result = run_action(
                    "update_status",
                    candidate_id = candidate_id,
                    new_status   = new_status,
                )
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success(f"✅ Statut mis à jour : **{new_status}**")
                    st.session_state["refresh_pipeline"] = True

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 14 — Recrutement automatisé · [GitHub](https://github.com/Rek1DSables/templates-ai)")