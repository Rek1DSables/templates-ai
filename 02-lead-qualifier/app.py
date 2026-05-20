# ============================================================
# APP — Pipeline de qualification de leads
# Interface Streamlit + LangGraph + Supabase
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client
from graph import build_graph
from config import (
    APP_TITLE, APP_SUBTITLE,
    LABEL_CHAUD, LABEL_TIEDE, LABEL_FROID
)
import os
import pandas as pd

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🎯", layout="centered")
st.title(APP_TITLE)
st.markdown(APP_SUBTITLE)

# ── Connexion Supabase ─────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase = get_supabase()

# ── Pipeline LangGraph ─────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return build_graph()

pipeline = get_pipeline()

# ── Formulaire ─────────────────────────────────────────────
with st.form("lead_form"):
    nom        = st.text_input("Nom du prospect")
    entreprise = st.text_input("Entreprise")
    email      = st.text_input("Email")
    message    = st.text_area("Message du prospect", height=150)
    submitted  = st.form_submit_button("Analyser le lead")

if submitted and nom and message:
    with st.spinner("Analyse en cours..."):
        try:
            result = pipeline.invoke({
                "lead": {"nom": nom, "entreprise": entreprise,
                         "email": email, "message": message},
                "score": 0,
                "category": "",
                "email_content": ""
            })

            score         = result["score"]
            category      = result["category"]
            email_content = result["email_content"]

            labels = {"chaud": LABEL_CHAUD, "tiede": LABEL_TIEDE, "froid": LABEL_FROID}

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Score", f"{score}/10")
            with col2:
                st.metric("Catégorie", labels.get(category, category))

            st.markdown("### Email suggéré")
            st.text_area("Réponse suggérée", email_content, height=200)

            if supabase:
                supabase.table("leads").insert({
                    "nom": nom, "entreprise": entreprise,
                    "email": email, "message": message,
                    "score": score, "category": category,
                    "email_content": email_content
                }).execute()
                st.success("✅ Lead sauvegardé dans la base de données")
            else:
                st.info("ℹ️ Supabase non configuré — lead non sauvegardé")

        except Exception as e:
            if "overloaded" in str(e).lower():
                st.error("⚠️ Le service est temporairement surchargé. Réessayez dans quelques secondes.")
            elif "api_key" in str(e).lower():
                st.error("🔑 Clé API invalide. Vérifiez votre fichier .env.")
            else:
                st.error("❌ Une erreur est survenue. Réessayez ou contactez le support.")

# ── Historique ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Historique des leads")

if supabase:
    data = supabase.table("leads").select("*").order("created_at", desc=True).execute()
    if data.data:
        df = pd.DataFrame(data.data)[["nom", "entreprise", "score", "category", "created_at"]]
        st.dataframe(df)
    else:
        st.info("Aucun lead enregistré pour l'instant.")
else:
    st.warning("⚠️ Supabase non configuré — historique indisponible.")