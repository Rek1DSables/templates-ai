import time
import json
import requests
from typing import TypedDict, Optional

import fitz
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase import create_client
from langgraph.graph import StateGraph, END

import config

# ─── LLM & Embeddings ────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

# ─── State ───────────────────────────────────────────────────────────────────
class RAGMultiState(TypedDict):
    # Input
    question:      str
    history:       list

    # Sources
    pdf_vectorstores:  Optional[list]   # liste de FAISS vectorstores
    supabase_table:    Optional[str]
    supabase_columns:  Optional[list]
    api_url:           Optional[str]
    api_key:           Optional[str]

    # Runtime
    pdf_context:       Optional[str]
    supabase_context:  Optional[str]
    api_context:       Optional[str]
    combined_context:  Optional[str]
    answer:            Optional[str]

    # Suivi
    sources_used: list
    errors:       list
    status:       str

# ─── Helpers ─────────────────────────────────────────────────────────────────
def invoke_with_retry(chain, input_data):
    for attempt in range(config.MAX_RETRIES):
        try:
            return chain.invoke(input_data)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < config.MAX_RETRIES - 1:
                time.sleep(config.RETRY_DELAY)
                continue
            raise

def extract_text_from_pdf(file_bytes: bytes) -> str:
    doc  = fitz.open(stream=file_bytes, filetype="pdf")
    return "".join([page.get_text() for page in doc])

def build_vectorstore(text: str) -> object:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = config.CHUNK_SIZE,
        chunk_overlap = config.CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)
    return FAISS.from_texts(chunks, embeddings)

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def retrieve_pdf_context(state: RAGMultiState) -> RAGMultiState:
    """Recherche dans les vectorstores PDF."""
    try:
        if not state.get("pdf_vectorstores"):
            return {**state, "pdf_context": None}

        all_chunks = []
        for vs in state["pdf_vectorstores"]:
            docs = vs.similarity_search(state["question"], k=config.TOP_K)
            all_chunks.extend([doc.page_content for doc in docs])

        pdf_context = "\n\n".join(all_chunks) if all_chunks else None
        sources_used = state["sources_used"] + ["PDF"] if pdf_context else state["sources_used"]

        return {**state, "pdf_context": pdf_context, "sources_used": sources_used}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Recherche PDF : {e}"]}


def retrieve_supabase_context(state: RAGMultiState) -> RAGMultiState:
    """Recherche dans Supabase."""
    try:
        if not state.get("supabase_table") or not config.SUPABASE_URL:
            return {**state, "supabase_context": None}

        sb      = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        columns = ", ".join(state["supabase_columns"]) if state.get("supabase_columns") else "*"
        result  = sb.table(state["supabase_table"]).select(columns).limit(50).execute()

        if not result.data:
            return {**state, "supabase_context": None}

        # Conversion en texte lisible
        rows_text = "\n".join([str(row) for row in result.data[:20]])
        supabase_context = f"Données Supabase ({state['supabase_table']}) :\n{rows_text}"
        sources_used = state["sources_used"] + ["Supabase"]

        return {**state, "supabase_context": supabase_context, "sources_used": sources_used}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Recherche Supabase : {e}"], "supabase_context": None}


def retrieve_api_context(state: RAGMultiState) -> RAGMultiState:
    """Récupère des données depuis une API externe."""
    try:
        if not state.get("api_url"):
            return {**state, "api_context": None}

        headers = {}
        if state.get("api_key"):
            headers["Authorization"] = f"Bearer {state['api_key']}"

        response = requests.get(state["api_url"], headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()
        api_context  = f"Données API ({state['api_url']}) :\n{json.dumps(data, ensure_ascii=False, indent=2)[:2000]}"
        sources_used = state["sources_used"] + ["API"]

        return {**state, "api_context": api_context, "sources_used": sources_used}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Récupération API : {e}"], "api_context": None}


def combine_contexts(state: RAGMultiState) -> RAGMultiState:
    """Combine tous les contextes disponibles."""
    parts = []

    if state.get("pdf_context"):
        parts.append(f"=== SOURCE PDF ===\n{state['pdf_context']}")
    if state.get("supabase_context"):
        parts.append(f"=== SOURCE SUPABASE ===\n{state['supabase_context']}")
    if state.get("api_context"):
        parts.append(f"=== SOURCE API ===\n{state['api_context']}")

    if not parts:
        return {**state, "errors": state["errors"] + ["Aucune source disponible."], "status": "error"}

    combined = "\n\n".join(parts)
    return {**state, "combined_context": combined}


def generate_answer(state: RAGMultiState) -> RAGMultiState:
    """Génère une réponse en citant les sources."""
    try:
        sources_list = ", ".join(state["sources_used"]) if state["sources_used"] else "aucune"

        history_text = ""
        for msg in state.get("history", [])[-6:]:
            role = "Utilisateur" if msg["role"] == "user" else "Assistant"
            history_text += f"{role} : {msg['content']}\n"

        system_prompt = f"""Tu es {config.CHATBOT_NAME}.
Tu réponds UNIQUEMENT à partir des contextes fournis.
Sources disponibles : {sources_list}
Pour chaque information clé, indique entre crochets la source utilisée : [PDF], [Supabase] ou [API].
Si la réponse n'est pas dans les sources, dis-le clairement.
Réponds en français, de manière concise et professionnelle.

CONTEXTES :
{state['combined_context']}
"""
        messages = [SystemMessage(content=system_prompt)]

        if history_text:
            messages.append(HumanMessage(content=f"Historique :\n{history_text}"))

        messages.append(HumanMessage(content=state["question"]))

        response = invoke_with_retry(llm, messages)
        return {**state, "answer": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Génération réponse : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(RAGMultiState)

    g.add_node("retrieve_pdf_context",      retrieve_pdf_context)
    g.add_node("retrieve_supabase_context", retrieve_supabase_context)
    g.add_node("retrieve_api_context",      retrieve_api_context)
    g.add_node("combine_contexts",          combine_contexts)
    g.add_node("generate_answer",           generate_answer)

    g.set_entry_point("retrieve_pdf_context")

    g.add_edge("retrieve_pdf_context",      "retrieve_supabase_context")
    g.add_edge("retrieve_supabase_context", "retrieve_api_context")
    g.add_edge("retrieve_api_context",      "combine_contexts")
    g.add_conditional_edges("combine_contexts", _stop_on_error("generate_answer"))
    g.add_edge("generate_answer", END)

    return g.compile()


def run_rag_multi(
    question:         str,
    history:          list,
    pdf_vectorstores: list  = None,
    supabase_table:   str   = None,
    supabase_columns: list  = None,
    api_url:          str   = None,
    api_key:          str   = None,
) -> RAGMultiState:
    initial_state = RAGMultiState(
        question          = question,
        history           = history,
        pdf_vectorstores  = pdf_vectorstores or [],
        supabase_table    = supabase_table,
        supabase_columns  = supabase_columns,
        api_url           = api_url,
        api_key           = api_key,
        pdf_context       = None,
        supabase_context  = None,
        api_context       = None,
        combined_context  = None,
        answer            = None,
        sources_used      = [],
        errors            = [],
        status            = "pending",
    )
    return build_graph().invoke(initial_state)