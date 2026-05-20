# ============================================================
# GRAPH — Agent support client multi-canal
# Logique : classification, scoring, réponse, escalade
# ============================================================

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from config import (
    MODEL, SCORE_AUTO_REPONSE, SCORE_ESCALADE,
    CATEGORIES, RESPONSE_TON, RESPONSE_LANGUE, SIGNATURE
)
import os
import time

# ── State ──────────────────────────────────────────────────
class TicketState(TypedDict):
    ticket: dict
    category: str
    priority: str
    score: int
    response: str
    escalade: bool

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

# ── Nodes ──────────────────────────────────────────────────
def classify(state: TicketState) -> TicketState:
    """Classifie le ticket et lui attribue une priorité et un score de confiance."""
    ticket = state["ticket"]
    llm = get_llm()
    categories_str = "\n".join([f"- {c}" for c in CATEGORIES])
    result = invoke_with_retry(llm, f"""
Analyse ce ticket support et réponds UNIQUEMENT en JSON valide :
{{
  "category": "une des catégories suivantes : {', '.join(CATEGORIES)}",
  "priority": "haute, moyenne ou basse",
  "score": nombre entier de 0 à 10 (confiance pour réponse automatique)
}}

Ticket : {ticket['message']}
Client : {ticket['nom']}
""")
    import json
    try:
        content = result.content.strip()
        if "```" in content:
            content = content.split("```")[1].replace("json", "").strip()
        data = json.loads(content)
        return {
            "category": data.get("category", "Autre"),
            "priority": data.get("priority", "moyenne"),
            "score": int(data.get("score", 5)),
        }
    except Exception:
        return {"category": "Autre", "priority": "moyenne", "score": 5}

def generate_response(state: TicketState) -> TicketState:
    """Génère une réponse draft au ticket."""
    ticket = state["ticket"]
    llm = get_llm()
    result = invoke_with_retry(llm, f"""
Tu es un agent support client. Ton : {RESPONSE_TON}. Langue : {RESPONSE_LANGUE}.
Rédige une réponse professionnelle et empathique à ce ticket.
Catégorie : {state['category']}
Message du client : {ticket['message']}
Termine par : {SIGNATURE}
""")
    return {"response": result.content.strip(), "escalade": False}

def escalate(state: TicketState) -> TicketState:
    """Marque le ticket pour escalade humaine."""
    return {
        "response": "Ce ticket nécessite une intervention humaine.",
        "escalade": True
    }

def route_ticket(state: TicketState) -> str:
    """Route selon le score de confiance."""
    if state["score"] >= SCORE_AUTO_REPONSE:
        return "auto"
    else:
        return "escalade"

# ── Graph factory ──────────────────────────────────────────
def build_graph():
    """Construit et compile le graphe LangGraph."""
    graph = StateGraph(TicketState)

    graph.add_node("classify",          classify)
    graph.add_node("generate_response", generate_response)
    graph.add_node("escalate",          escalate)

    graph.add_edge(START, "classify")
    graph.add_conditional_edges("classify", route_ticket, {
        "auto"    : "generate_response",
        "escalade": "escalate",
    })
    graph.add_edge("generate_response", END)
    graph.add_edge("escalate",          END)

    return graph.compile()