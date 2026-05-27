import time
from typing import TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph, END
import fitz  # PyMuPDF

import config

# ─── LLM & Embeddings ────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=1024,
)

embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)

# ─── State ───────────────────────────────────────────────────────────────────
class RAGState(TypedDict):
    # Input
    question:     str
    file_bytes:   Optional[bytes]
    file_name:    Optional[str]

    # Runtime
    vectorstore:  Optional[object]
    context:      Optional[str]
    answer:       Optional[str]

    # Historique conversation
    history:      list  # [{"role": "user"|"assistant", "content": str}]

    # Suivi
    errors: list
    status: str

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

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extrait le texte d'un PDF via PyMuPDF."""
    doc  = fitz.open(stream=file_bytes, filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def build_vectorstore(text: str) -> object:
    """Découpe le texte en chunks et construit le vectorstore FAISS."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size    = config.CHUNK_SIZE,
        chunk_overlap = config.CHUNK_OVERLAP,
    )
    chunks = splitter.split_text(text)
    return FAISS.from_texts(chunks, embeddings)

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def load_document(state: RAGState) -> RAGState:
    """Charge et indexe le document PDF."""
    try:
        if state.get("vectorstore"):
            return state  # document déjà chargé

        if not state.get("file_bytes"):
            return {**state, "errors": ["Aucun document fourni."], "status": "error"}

        text = extract_text_from_pdf(state["file_bytes"])
        if not text.strip():
            return {**state, "errors": ["Le document est vide ou illisible."], "status": "error"}

        vectorstore = build_vectorstore(text)
        return {**state, "vectorstore": vectorstore, "status": "loaded"}

    except Exception as e:
        return {**state, "errors": [f"Chargement document : {e}"], "status": "error"}


def retrieve_context(state: RAGState) -> RAGState:
    """Recherche les chunks les plus pertinents pour la question."""
    try:
        docs    = state["vectorstore"].similarity_search(state["question"], k=config.TOP_K)
        context = "\n\n".join([doc.page_content for doc in docs])
        return {**state, "context": context}

    except Exception as e:
        return {**state, "errors": [f"Recherche contexte : {e}"], "status": "error"}


def generate_answer(state: RAGState) -> RAGState:
    """Génère une réponse basée sur le contexte récupéré."""
    try:
        # Construction de l'historique pour le LLM
        history_text = ""
        for msg in state.get("history", [])[-6:]:  # 3 derniers échanges
            role    = "Utilisateur" if msg["role"] == "user" else "Assistant"
            history_text += f"{role} : {msg['content']}\n"

        system_prompt = f"""Tu es {config.CHATBOT_NAME} pour {config.COMPANY_NAME}.
Tu réponds UNIQUEMENT à partir du contexte fourni.
Si la réponse n'est pas dans le contexte, dis-le clairement.
Réponds en français, de manière concise et professionnelle.

CONTEXTE DOCUMENT :
{state['context']}
"""
        messages = [SystemMessage(content=system_prompt)]

        if history_text:
            messages.append(HumanMessage(content=f"Historique de conversation :\n{history_text}"))

        messages.append(HumanMessage(content=state["question"]))

        response = invoke_with_retry(llm, messages)
        return {**state, "answer": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Génération réponse : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(RAGState)

    g.add_node("load_document",    load_document)
    g.add_node("retrieve_context", retrieve_context)
    g.add_node("generate_answer",  generate_answer)

    g.set_entry_point("load_document")

    g.add_conditional_edges("load_document",    _stop_on_error("retrieve_context"))
    g.add_conditional_edges("retrieve_context", _stop_on_error("generate_answer"))
    g.add_edge("generate_answer", END)

    return g.compile()


def run_rag(question: str, file_bytes: bytes, file_name: str, vectorstore, history: list) -> RAGState:
    initial_state = RAGState(
        question    = question,
        file_bytes  = file_bytes,
        file_name   = file_name,
        vectorstore = vectorstore,
        context     = None,
        answer      = None,
        history     = history,
        errors      = [],
        status      = "pending",
    )
    return build_graph().invoke(initial_state)