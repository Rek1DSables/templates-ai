import streamlit as st
from graph import run_rag_multi, extract_text_from_pdf, build_vectorstore
import config

st.set_page_config(
    page_title="RAG Multi-Sources",
    page_icon="🔗",
    layout="wide",
)

st.title("🔗 Système RAG Multi-Sources")
st.caption(f"LangGraph · FAISS · Supabase · API · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Session state ───────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history          = []
if "pdf_vectorstores" not in st.session_state:
    st.session_state.pdf_vectorstores = []
if "pdf_names" not in st.session_state:
    st.session_state.pdf_names        = []

# ─── Sidebar — Configuration des sources ─────────────────────────────────────
with st.sidebar:
    st.subheader("🔗 Sources de données")

    # ── PDFs ──────────────────────────────────────────────────────────────────
    st.markdown("**📄 PDFs**")
    uploaded_files = st.file_uploader("Uploadez un ou plusieurs PDFs", type=["pdf"], accept_multiple_files=True)

    if uploaded_files:
        for file in uploaded_files:
            if file.name not in st.session_state.pdf_names:
                with st.spinner(f"Indexation de {file.name}..."):
                    try:
                        text = extract_text_from_pdf(file.read())
                        vs   = build_vectorstore(text)
                        st.session_state.pdf_vectorstores.append(vs)
                        st.session_state.pdf_names.append(file.name)
                        st.success(f"✅ {file.name}")
                    except Exception as e:
                        st.error(f"Erreur : {e}")

    if st.session_state.pdf_names:
        st.caption(f"PDFs chargés : {', '.join(st.session_state.pdf_names)}")

    st.markdown("---")

    # ── Supabase ──────────────────────────────────────────────────────────────
    st.markdown("**🗄️ Supabase**")
    supabase_table   = st.text_input("Table", placeholder="ma_table")
    supabase_columns = st.text_input("Colonnes (séparées par des virgules)", placeholder="id, nom, description")

    st.markdown("---")

    # ── API externe ───────────────────────────────────────────────────────────
    st.markdown("**🌐 API externe**")
    api_url = st.text_input("URL de l'API", placeholder="https://api.exemple.com/data")
    api_key = st.text_input("Clé API (optionnel)", type="password")

    st.markdown("---")

    # ── Sources actives ───────────────────────────────────────────────────────
    sources_active = []
    if st.session_state.pdf_vectorstores:
        sources_active.append(f"📄 {len(st.session_state.pdf_names)} PDF(s)")
    if supabase_table:
        sources_active.append(f"🗄️ Supabase : {supabase_table}")
    if api_url:
        sources_active.append(f"🌐 API")

    if sources_active:
        st.markdown("**Sources actives :**")
        for s in sources_active:
            st.markdown(f"- {s}")
    else:
        st.warning("Aucune source configurée.")

    if st.button("🗑️ Réinitialiser", use_container_width=True):
        st.session_state.history          = []
        st.session_state.pdf_vectorstores = []
        st.session_state.pdf_names        = []
        st.rerun()

# ─── Interface chat ───────────────────────────────────────────────────────────
if not sources_active:
    st.info(config.WELCOME_MESSAGE, icon="ℹ️")
else:
    # Historique
    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    question = st.chat_input("Posez votre question...")

    if question:
        st.session_state.history.append({"role": "user", "content": question})
        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):
            with st.spinner("Recherche dans les sources..."):
                try:
                    result = run_rag_multi(
                        question         = question,
                        history          = st.session_state.history,
                        pdf_vectorstores = st.session_state.pdf_vectorstores,
                        supabase_table   = supabase_table or None,
                        supabase_columns = [c.strip() for c in supabase_columns.split(",")] if supabase_columns else None,
                        api_url          = api_url or None,
                        api_key          = api_key or None,
                    )

                    if result["status"] == "error":
                        answer = f"❌ {result['errors'][0]}"
                    else:
                        answer = result.get("answer", "Aucune réponse générée.")
                        sources = result.get("sources_used", [])
                        if sources:
                            answer += f"\n\n*Sources consultées : {', '.join(sources)}*"

                    st.markdown(answer)
                    st.session_state.history.append({"role": "assistant", "content": answer})

                    if result.get("errors"):
                        with st.expander("⚠️ Avertissements"):
                            for err in result["errors"]:
                                st.warning(err)

                except Exception as e:
                    st.error(f"Erreur inattendue : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 19 — RAG Multi-Sources · [GitHub](https://github.com/Rek1DSables/templates-ai)")