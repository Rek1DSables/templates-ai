# ============================================================
# APP — Agent support client multi-canal
# Interface Streamlit + LangGraph + Supabase
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from supabase import create_client
from graph import build_graph
from config import APP_TITLE, APP_SUBTITLE, PRIORITIES
import os
import pandas as pd

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="🎧", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Connexion Supabase ─────────────────────────────────────
@st.cache_resource
def get_supabase():
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")
    if url and key:
        return create_client(url, key)
    return None

supabase = get_supabase()

# ── Pipeline ───────────────────────────────────────────────
@st.cache_resource
def get_pipeline():
    return build_graph()

pipeline = get_pipeline()

# ── Formulaire ─────────────────────────────────────────────
with st.form("ticket_form"):
    nom       = st.text_input("Nom du client")
    email     = st.text_input("Email")
    message   = st.text_area("Message du client", height=150)
    submitted = st.form_submit_button("Analyser le ticket")

if submitted and nom and message:
    with st.spinner("Analyse du ticket en cours..."):
        try:
            result = pipeline.invoke({
                "ticket"  : {"nom": nom, "email": email, "message": message},
                "category": "",
                "priority": "",
                "score"   : 0,
                "response": "",
                "escalade": False,
            })

            category = result["category"]
            priority = result["priority"]
            score    = result["score"]
            response = result["response"]
            escalade = result["escalade"]

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Catégorie", category)
            with col2:
                st.metric("Priorité", PRIORITIES.get(priority, priority))
            with col3:
                st.metric("Score confiance", f"{score}/10")

            st.markdown("---")

            if escalade:
                st.error("🚨 Escalade requise — intervention humaine nécessaire.")
            else:
                st.success("✅ Réponse automatique générée")

            st.markdown("### 📧 Réponse draft")
            st.text_area("Réponse suggérée", response, height=200)

            if supabase:
                supabase.table("tickets").insert({
                    "nom"     : nom,
                    "email"   : email,
                    "message" : message,
                    "category": category,
                    "priority": priority,
                    "score"   : score,
                    "response": response,
                    "escalade": escalade,
                }).execute()
                st.success("✅ Ticket sauvegardé dans la base de données")
            else:
                st.info("ℹ️ Supabase non configuré — ticket non sauvegardé")

        except Exception as e:
            if "overloaded" in str(e).lower():
                st.error("⚠️ Le service est temporairement surchargé. Réessayez dans quelques secondes.")
            elif "api_key" in str(e).lower():
                st.error("🔑 Clé API invalide. Vérifiez votre fichier .env.")
            else:
                st.error("❌ Une erreur est survenue. Réessayez ou contactez le support.")

# ── Historique ─────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📋 Historique des tickets")

if supabase:
    try:
        data = supabase.table("tickets").select("*").order("created_at", desc=True).execute()
        if data.data:
            df = pd.DataFrame(data.data)[["nom", "email", "category", "priority", "score", "escalade", "created_at"]]
            st.dataframe(df)
        else:
            st.info("Aucun ticket enregistré pour l'instant.")
    except Exception as e:
        if "overloaded" in str(e).lower():
            st.error("⚠️ Le service est temporairement surchargé. Réessayez dans quelques secondes.")
        elif "api_key" in str(e).lower():
            st.error("🔑 Clé API invalide. Vérifiez votre fichier .env.")
        else:
            st.warning("⚠️ Impossible de charger l'historique. Vérifiez votre configuration Supabase.")
else:
    st.warning("⚠️ Supabase non configuré — historique indisponible.")