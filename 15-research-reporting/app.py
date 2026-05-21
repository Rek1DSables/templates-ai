import streamlit as st
from crew import run_research
import config

st.set_page_config(
    page_title="Research & Reporting",
    page_icon="🔬",
    layout="centered",
)

st.title("🔬 Système Multi-Agents Research & Reporting")
st.caption(f"CrewAI · Serper · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Entrez un sujet de recherche. 4 agents IA vont collaborer pour produire un rapport complet :\n"
    "1. 🔍 **Searcher** — collecte les informations via Google\n"
    "2. 📊 **Analyst** — analyse et identifie les tendances\n"
    "3. ✍️ **Writer** — rédige le rapport structuré\n"
    "4. 🔎 **Critic** — révise et améliore le rapport final",
    icon="ℹ️",
)

st.warning("⏱️ Ce pipeline prend 3 à 5 minutes — 4 agents travaillent en séquence.", icon="⚠️")

# ─── Formulaire ──────────────────────────────────────────────────────────────
with st.form("research_form"):
    topic = st.text_input(
        "Sujet de recherche *",
        placeholder="Ex : Marché de l'IA générative en France 2024 | Tesla | Secteur de la fintech européenne",
    )
    submitted = st.form_submit_button("🚀 Lancer la recherche", use_container_width=True, type="primary")

# ─── Pipeline ────────────────────────────────────────────────────────────────
if submitted:
    if not topic:
        st.error("⚠️ Le sujet de recherche est obligatoire.")
        st.stop()

    with st.status("⚙️ Pipeline multi-agents en cours...", expanded=True) as pipeline_status:
        st.write("🔍 Searcher — collecte des informations...")
        st.write("📊 Analyst — analyse des données...")
        st.write("✍️ Writer — rédaction du rapport...")
        st.write("🔎 Critic — révision finale...")

        try:
            result = run_research(topic=topic)

            if result["status"] == "error":
                pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                for err in result["errors"]:
                    st.error(err)

            elif result["status"] == "completed":
                pipeline_status.update(label="✅ Rapport généré !", state="complete", expanded=False)

                st.success(f"✅ Rapport sur **{topic}** généré avec succès.")
                st.markdown("---")

                st.subheader("📄 Rapport final")
                st.markdown(result.get("report", "—"))

                st.download_button(
                    label="⬇️ Télécharger le rapport",
                    data=result.get("report", ""),
                    file_name=f"rapport_{topic[:30].replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            else:
                pipeline_status.update(label="⚠️ Erreur inattendue", state="error")

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 15 — Research & Reporting · [GitHub](https://github.com/Rek1DSables/templates-ai)")