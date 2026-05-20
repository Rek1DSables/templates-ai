# ============================================================
# GRAPH — Agent extraction de données web
# Logique : scraping, nettoyage, extraction structurée
# ============================================================

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from config import MODEL, OUTPUT_LANGUE, MAX_CHARS
import os
import time
import requests
from bs4 import BeautifulSoup

# ── State ──────────────────────────────────────────────────
class ExtractState(TypedDict):
    url: str
    raw_text: str
    format_instruction: str
    result: str

# ── LLM ───────────────────────────────────────────────────
def get_llm():
    return ChatAnthropic(
        model=MODEL,
        api_key=os.getenv("ANTHROPIC_API_KEY")
    )

# ── Retry ──────────────────────────────────────────────────
def invoke_with_retry(llm, prompt, retries=3, delay=5):
    for attempt in range(retries):
        try:
            return llm.invoke(prompt)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < retries - 1:
                time.sleep(delay)
            else:
                raise e

# ── Scraping ───────────────────────────────────────────────
def scrape_url(url: str) -> str:
    """Scrape le contenu texte d'une URL."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    # Supprime les balises inutiles
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    # Nettoie les lignes vides multiples
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

# ── Nodes ──────────────────────────────────────────────────
def scrape(state: ExtractState) -> ExtractState:
    """Scrape le contenu de l'URL."""
    raw_text = scrape_url(state["url"])
    return {"raw_text": raw_text}

def extract(state: ExtractState) -> ExtractState:
    """Extrait et structure les données selon le format choisi."""
    llm = get_llm()
    prompt = f"""Tu es un expert en extraction et structuration de données web.
Langue de réponse : {OUTPUT_LANGUE}.
Format demandé : {state['format_instruction']}

Contenu de la page web :
{state['raw_text'][:MAX_CHARS]}

Extrais et structure les données selon le format demandé.
"""
    result = invoke_with_retry(llm, prompt)
    return {"result": result.content.strip()}

# ── Graph factory ──────────────────────────────────────────
def build_graph():
    """Construit et compile le graphe LangGraph."""
    graph = StateGraph(ExtractState)
    graph.add_node("scrape",  scrape)
    graph.add_node("extract", extract)
    graph.add_edge(START,     "scrape")
    graph.add_edge("scrape",  "extract")
    graph.add_edge("extract", END)
    return graph.compile()