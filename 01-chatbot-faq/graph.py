# ============================================================
# GRAPH — Chatbot FAQ intelligent
# Logique RAG : chargement docs, vectorisation, recherche, réponse
# ============================================================

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_anthropic import ChatAnthropic
from langchain_huggingface import HuggingFaceEmbeddings
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from config import MODEL, TOP_K, CHUNK_SIZE, CHUNK_OVERLAP, NO_ANSWER_MSG, EMBEDDING_MODEL
import os

# ── State ──────────────────────────────────────────────────
class ChatState(TypedDict):
    question: str
    context: str
    answer: str

# ── LLM ───────────────────────────────────────────────────
def get_llm():
    return ChatAnthropic(
        model=MODEL,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# ── Vectorstore ────────────────────────────────────────────
def build_vectorstore(docs_folder: str):
    """Charge tous les PDFs du dossier et construit l'index FAISS."""
    documents = []
    for filename in os.listdir(docs_folder):
        if filename.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(docs_folder, filename))
            documents.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(documents)

    embeddings = HuggingFaceEmbeddings(
    model_name=EMBEDDING_MODEL
)
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return vectorstore

# ── Nodes ──────────────────────────────────────────────────
def retrieve(state: ChatState, vectorstore) -> ChatState:
    """Recherche les chunks les plus pertinents."""
    docs = vectorstore.similarity_search(state["question"], k=TOP_K)
    context = "\n\n".join([doc.page_content for doc in docs])
    return {"context": context}

def generate(state: ChatState) -> ChatState:
    """Génère la réponse à partir du contexte récupéré."""
    llm = get_llm()
    prompt = f"""Tu es un assistant FAQ. Réponds uniquement à partir du contexte fourni.
Si la réponse n'est pas dans le contexte, dis-le clairement.

Contexte :
{state['context']}

Question : {state['question']}

Réponse :"""
    result = llm.invoke(prompt)
    answer = result.content.strip() if result.content.strip() else NO_ANSWER_MSG
    return {"answer": answer}

# ── Graph factory ──────────────────────────────────────────
def build_graph(vectorstore):
    """Construit et compile le graphe LangGraph."""

    def retrieve_node(state):
        return retrieve(state, vectorstore)

    graph = StateGraph(ChatState)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph.compile()