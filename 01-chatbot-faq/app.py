# ============================================================
# APP — Chatbot FAQ intelligent
# Interface Streamlit + pipeline RAG LangGraph
# ============================================================

import streamlit as st
from dotenv import load_dotenv
from graph import build_vectorstore, build_graph
from config import APP_TITLE, APP_SUBTITLE, DOCS_FOLDER, NO_ANSWER_MSG
import os

load_dotenv()

# ── Page config ────────────────────────────────────────────
st.set_page_config(page_title=APP_TITLE, page_icon="💬", layout="centered")
st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

# ── Chargement vectorstore (mis en cache) ──────────────────
@st.cache_resource
def load_pipeline():
    if not os.path.exists(DOCS_FOLDER) or not os.listdir(DOCS_FOLDER):
        return None
    vectorstore = build_vectorstore(DOCS_FOLDER)
    return build_graph(vectorstore)

pipeline = load_pipeline()

# ── Vérification dossier docs ──────────────────────────────
if pipeline is None:
    st.warning(f"⚠️ Aucun PDF trouvé dans le dossier `{DOCS_FOLDER}/`. Ajoutez vos documents et relancez l'app.")
    st.stop()

# ── Historique conversation ────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ── Input utilisateur ──────────────────────────────────────
question = st.chat_input("Posez votre question...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Recherche en cours..."):
            result = pipeline.invoke({
                "question": question,
                "context": "",
                "answer": ""
            })
            answer = result.get("answer", NO_ANSWER_MSG)
        st.write(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})