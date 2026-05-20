# ============================================================
# APP — Agent extraction de données web
# Interface Streamlit + pipeline LangGraph
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from graph import build_graph
from config import APP_TITLE, APP_SUBTITLE, EXTRACT_FORMATS
import os

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🌐", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Pipeline ───────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return build_graph()

pipeline = get_pipeline()

# ── Formulaire ─────────────────────────────────────────────
url          = st.text_input("URL à analyser", placeholder="https://example.com")
format_label = st.selectbox("Format d'extraction", list(EXTRACT_FORMATS.keys()))

if url and st.button("Extraire les données"):
    with st.spinner("Extraction en cours..."):
        try:
            result = pipeline.invoke({
                "url"                : url,
                "raw_text"           : "",
                "format_instruction" : EXTRACT_FORMATS[format_label],
                "result"             : ""
            })

            data = result["result"]

            st.markdown("---")
            st.markdown("### 📊 Données extraites")
            st.markdown(data)

            st.download_button(
                label="⬇️ Télécharger les données",
                data=data,
                file_name="extraction_web.txt",
                mime="text/plain"
            )

        except Exception as e:
            if "overloaded" in str(e).lower():
                st.error("⚠️ Le service est temporairement surchargé. Réessayez dans quelques secondes.")
            elif "api_key" in str(e).lower():
                st.error("🔑 Clé API invalide. Vérifiez votre fichier .env.")
            elif "connexion" in str(e).lower() or "timeout" in str(e).lower():
                st.error("🌐 Impossible d'accéder à l'URL. Vérifiez l'adresse et réessayez.")
            else:
                st.error("❌ Une erreur est survenue. Réessayez ou contactez le support.")