# ============================================================
# APP — Agent de veille concurrentielle
# Interface Streamlit + pipeline CrewAI 3 agents
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from crew import build_crew
from config import APP_TITLE, APP_SUBTITLE, RAPPORT_LENGTHS
import os

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🔍", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Formulaire ─────────────────────────────────────────────
with st.form("watch_form"):
    client       = st.text_input("Votre entreprise / client",
                    placeholder="Ex: Shark AI Consulting")
    secteur      = st.text_input("Secteur d'activité",
                    placeholder="Ex: Automatisation IA pour PME")
    concurrents  = st.text_area("Concurrents à analyser (un par ligne)", height=120,
                    placeholder="Concurrent A\nConcurrent B\nConcurrent C")
    length_label = st.selectbox("Longueur du rapport", list(RAPPORT_LENGTHS.keys()))
    submitted    = st.form_submit_button("Lancer la veille")

if submitted and client and secteur and concurrents:
    liste_concurrents = [c.strip() for c in concurrents.split("\n") if c.strip()]

    if not liste_concurrents:
        st.warning("⚠️ Ajoutez au moins un concurrent.")
    else:
        with st.spinner(f"Analyse de {len(liste_concurrents)} concurrent(s)... 60 à 90 secondes."):
            crew   = build_crew(
                liste_concurrents,
                secteur,
                client,
                RAPPORT_LENGTHS[length_label]
            )
            result = crew.kickoff()

        rapport = result.raw if hasattr(result, "raw") else str(result)

        st.markdown("---")
        st.markdown("### 📊 Rapport de veille")
        st.markdown(rapport)

        st.download_button(
            label="⬇️ Télécharger le rapport",
            data=rapport,
            file_name="rapport_veille_concurrentielle.txt",
            mime="text/plain"
        )