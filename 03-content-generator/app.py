# ============================================================
# APP — Générateur de contenu marketing
# Interface Streamlit + pipeline CrewAI 3 agents
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from crew import build_crew
from config import (
    APP_TITLE, APP_SUBTITLE,
    CONTENT_TYPES, LANGUAGES, TONES, LENGTHS
)
import os

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="✍️", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Formulaire ─────────────────────────────────────────────
with st.form("content_form"):
    brief        = st.text_area("Brief / Sujet", height=100,
                    placeholder="Ex: Les avantages de l'automatisation IA pour les PME")
    content_type = st.selectbox("Type de contenu", CONTENT_TYPES)
    tone         = st.selectbox("Tonalité", TONES)
    language     = st.selectbox("Langue", LANGUAGES)
    length_label = st.selectbox("Longueur", list(LENGTHS.keys()))
    submitted    = st.form_submit_button("Générer le contenu")

if submitted and brief:
    length = LENGTHS[length_label]

    with st.spinner("Les agents travaillent... ça peut prendre 30 à 60 secondes."):
        crew   = build_crew(brief, content_type, tone, language, length)
        result = crew.kickoff()

    st.markdown("---")
    st.markdown("### 📄 Contenu généré")
    st.markdown(result.raw if hasattr(result, "raw") else str(result))

    # ── Bouton téléchargement ──────────────────────────────
    content_str = result.raw if hasattr(result, "raw") else str(result)
    st.download_button(
        label="⬇️ Télécharger le contenu",
        data=content_str,
        file_name=f"{content_type.lower().replace(' ', '_')}.txt",
        mime="text/plain"
    )