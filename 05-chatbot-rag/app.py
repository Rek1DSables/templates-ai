import streamlit as st
from graph import run_rag, build_vectorstore, extract_text_from_pdf
import config

st.set_page_config(
    page_title=config.CHATBOT_NAME,
    page_icon="📚",
    layout="centered",
)

st.title("📚 Chatbot RAG — Documentation Technique")
st.caption(f"LangGraph · FAISS · HuggingFace · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Session state ───────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history     = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "file_name" not in st.session_state:
    st.session_state.file_name   = None
if "file_bytes" not in st.session_state:
    st.session_state.file_bytes  = None

# ─── Upload document ─────────────────────────────────────────────────────────
with st.sidebar:
    st.subheader("📄 Document")
    uploaded_file = st.file_uploader("Uploadez un PDF", type=["pdf"])

    if uploaded_file:
        file_bytes = uploaded_file.read()
        if file_bytes != st.session_state.file_bytes:
            with st.spinner("Indexation du document..."):
                try:
                    text = extract_text_from_pdf(file_bytes)
                    vectorstore = build_vectorstore(text)
                    st.session_state.vectorstore = vectorstore
                    st.session_state.file_bytes  = file_bytes
                    st.session_state.file_name   = uploaded_file.name
                    st.session_state.history     = []
                    st.success(f"✅ {uploaded_file.name} indexé !")
                except Exception as e:
                    st.error(f"Erreur : {e}")

    if st.session_state.file_name:
        st.caption(f"📄 Document actif : `{st.session_state.file_name}`")

    if st.button("🗑️ Réinitialiser", use_container_width=True):
        st.session_state.history     = []
        st.session_state.vectorstore = None
        st.session_state.file_name   = None
        st.session_state.file_bytes  = None
        st.rerun()

# ─── Affichage historique ─────────────────────────────────────────────────────
if not st.session_state.vectorstore:
    st.info(config.WELCOME_MESSAGE + "\n\nCommencez par uploader un document PDF dans le panneau gauche.", icon="ℹ️")
else:
    # Historique de conversation
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # ─── Input utilisateur ────────────────────────────────────────────────────
    question = st.chat_input("Posez votre question...")

    if question:
        # Affiche la question
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        # Pipeline RAG
        with st.chat_message("assistant"):
            with st.spinner("Recherche en cours..."):
                try:
                    result = run_rag(
                        question    = question,
                        file_bytes  = st.session_state.file_bytes,
                        file_name   = st.session_state.file_name,
                        vectorstore = st.session_state.vectorstore,
                        history     = st.session_state.history,
                    )

                    if result["status"] == "error":
                        answer = f"❌ {result['errors'][0]}"
                    else:
                        answer = result.get("answer", "Aucune réponse générée.")

                    st.markdown(answer)
                    st.session_state.history.append({"role": "assistant", "content": answer})

                    # Mise à jour vectorstore si recréé
                    if result.get("vectorstore"):
                        st.session_state.vectorstore = result["vectorstore"]

                except Exception as e:
                    st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 12 — Chatbot RAG · [GitHub](https://github.com/Rek1DSables/templates-ai)")