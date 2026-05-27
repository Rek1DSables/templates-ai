# app.py
import streamlit as st
from supabase import create_client
from graph import build_graph
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE,
    LANGUES_SUPPORTEES, BASE_CONNAISSANCE_DEFAUT
)

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")

# Init session state
if "historique" not in st.session_state:
    st.session_state.historique = []
if "messages_affichage" not in st.session_state:
    st.session_state.messages_affichage = []


def sauvegarder_supabase(data: dict):
    if not supabase:
        return
    try:
        supabase.table(SUPABASE_TABLE).insert(data).execute()
    except Exception as e:
        pass


# --- UI ---
st.set_page_config(page_title="Chatbot Multilingue AI", page_icon="🌍", layout="wide")
st.title("🌍 Chatbot Multilingue AI")
st.caption("Detection automatique de la langue + reponse dans la langue de l'utilisateur")

with st.sidebar:
    st.subheader("Configuration")
    st.caption(f"Langues supportees : {', '.join(LANGUES_SUPPORTEES[:6])} et plus")

    base_connaissance = st.text_area(
        "Base de connaissance",
        value=BASE_CONNAISSANCE_DEFAUT,
        height=300,
    )

    if st.button("Reinitialiser la conversation", use_container_width=True):
        st.session_state.historique = []
        st.session_state.messages_affichage = []
        st.rerun()

    st.divider()
    st.caption("Testez en plusieurs langues :")
    st.caption("FR : Comment fonctionne votre produit ?")
    st.caption("EN : What are your pricing plans ?")
    st.caption("ES : Cuanto cuesta el producto ?")
    st.caption("DE : Wie kann ich den Support kontaktieren ?")

# Affichage de la conversation
for msg in st.session_state.messages_affichage:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant" and "langue" in msg:
            st.caption(f"Langue detectee : {msg['langue']}")
        st.markdown(msg["content"])

# Input utilisateur
message = st.chat_input("Ecrivez votre message dans n'importe quelle langue...")

if message:
    # Afficher le message utilisateur
    st.session_state.messages_affichage.append({
        "role": "user",
        "content": message,
    })
    with st.chat_message("user"):
        st.markdown(message)

    # Generer la reponse
    with st.chat_message("assistant"):
        with st.spinner("..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "message_utilisateur": message,
                    "historique": st.session_state.historique,
                    "base_connaissance": base_connaissance,
                    "langue_detectee": "",
                    "reponse": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        st.caption(f"Langue detectee : {result['langue_detectee']}")
        st.markdown(result["reponse"])

    # Mettre a jour l'historique
    st.session_state.historique.append({
        "user": message,
        "assistant": result["reponse"],
    })
    st.session_state.messages_affichage.append({
        "role": "assistant",
        "content": result["reponse"],
        "langue": result["langue_detectee"],
    })

    # Sauvegarder
    sauvegarder_supabase({
        "message": message,
        "langue_detectee": result["langue_detectee"],
        "reponse": result["reponse"],
    })