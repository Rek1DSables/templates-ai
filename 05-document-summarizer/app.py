# ============================================================
# APP — Résumeur automatique de documents
# Interface Streamlit + pipeline LangGraph
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from graph import build_graph, extract_text_from_pdf
from config import APP_TITLE, APP_SUBTITLE, OUTPUT_FORMATS
import os

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="📄", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Pipeline ───────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return build_graph()

pipeline = get_pipeline()

# ── Formulaire ─────────────────────────────────────────────
uploaded_file = st.file_uploader("Uploadez votre PDF", type=["pdf"])
format_label  = st.selectbox("Format de sortie", list(OUTPUT_FORMATS.keys()))

if uploaded_file and st.button("Générer le résumé"):
    with st.spinner("Analyse du document en cours..."):
        try:
            text               = extract_text_from_pdf(uploaded_file)
            format_instruction = OUTPUT_FORMATS[format_label]

            result = pipeline.invoke({
                "text"               : text,
                "format_instruction" : format_instruction,
                "summary"            : ""
            })

            summary = result["summary"]

            st.markdown("---")
            st.markdown("### 📋 Résumé généré")
            st.markdown(summary)

            st.download_button(
                label="⬇️ Télécharger le résumé",
                data=summary,
                file_name="resume_document.txt",
                mime="text/plain"
            )

        except Exception as e:
            if "overloaded" in str(e).lower():
                st.error("⚠️ Le service est temporairement surchargé. Réessayez dans quelques secondes.")
            elif "api_key" in str(e).lower():
                st.error("🔑 Clé API invalide. Vérifiez votre fichier .env.")
            else:
                st.error("❌ Une erreur est survenue. Réessayez ou contactez le support.")