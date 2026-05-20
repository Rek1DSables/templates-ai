# ============================================================
# GRAPH — Résumeur automatique de documents
# Logique : extraction texte, découpage, résumé
# ============================================================

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from config import MODEL, CHUNK_SIZE, CHUNK_OVERLAP, OUTPUT_LANGUE
import os
import tempfile
import time

# ── State ──────────────────────────────────────────────────
class SummaryState(TypedDict):
    text: str
    format_instruction: str
    summary: str

# ── LLM ───────────────────────────────────────────────────
def get_llm():
    return ChatAnthropic(
        model=MODEL,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# ── Retry ─────────────────────────────────────────────────
def invoke_with_retry(llm, prompt, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

# ── Extraction PDF ─────────────────────────────────────────
def extract_text_from_pdf(uploaded_file) -> str:
    """Extrait le texte d'un PDF uploadé via Streamlit."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(uploaded_file.read())
        tmp_path = tmp.name

    loader = PyPDFLoader(tmp_path)
    pages  = loader.load()
    os.unlink(tmp_path)

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    chunks = splitter.split_documents(pages)
    return "\n\n".join([c.page_content for c in chunks])

# ── Nodes ──────────────────────────────────────────────────
def summarize(state: SummaryState) -> SummaryState:
    """Génère le résumé selon le format choisi."""
    llm = get_llm()
    prompt = f"""Tu es un expert en synthèse de documents.
Langue de réponse : {OUTPUT_LANGUE}.
Format demandé : {state['format_instruction']}

Document à analyser :
{state['text'][:12000]}

Produis le résumé demandé, complet et structuré.
"""
    result = invoke_with_retry(llm, prompt)
    return {"summary": result.content.strip()}

# ── Graph factory ──────────────────────────────────────────
def build_graph():
    """Construit et compile le graphe LangGraph."""
    graph = StateGraph(SummaryState)
    graph.add_node("summarize", summarize)
    graph.add_edge(START, "summarize")
    graph.add_edge("summarize", END)
    return graph.compile()