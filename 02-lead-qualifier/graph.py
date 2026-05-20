# ============================================================
# GRAPH — Pipeline de qualification de leads
# Logique : scoring, routing, génération email
# ============================================================

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from typing import TypedDict
from config import (
    MODEL, SCORE_CHAUD, SCORE_TIEDE,
    CRITERES, EMAIL_CHAUD_MOTS, EMAIL_TIEDE_MOTS,
    LABEL_CHAUD, LABEL_TIEDE, LABEL_FROID
)
import os
import time

# ── State ──────────────────────────────────────────────────
class LeadState(TypedDict):
    lead: dict
    score: int
    category: str
    email_content: str

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
def score_lead(state: LeadState) -> LeadState:
    """Score le lead de 0 à 10 selon les critères définis."""
    lead = state["lead"]
    llm = get_llm()
    result = invoke_with_retry(llm, f"""
Analyse ce message d'un prospect et donne-lui un score de 0 à 10.
Critères :
{CRITERES}
Réponds UNIQUEMENT avec un nombre entier entre 0 et 10.
Message : {lead['message']}
""")
    try:
        score = int(result.content.strip())
        score = max(0, min(10, score))
    except ValueError:
        score = 0
    return {"score": score}

def route_lead(state: LeadState) -> LeadState:
    """Route le lead selon son score."""
    score = state["score"]
    if score >= SCORE_CHAUD:
        category = "chaud"
    elif score >= SCORE_TIEDE:
        category = "tiede"
    else:
        category = "froid"
    return {"category": category}

def email_contact(state: LeadState) -> LeadState:
    """Génère un email de prise de contact pour un lead chaud."""
    lead = state["lead"]
    llm = get_llm()
    result = invoke_with_retry(llm, f"""
Tu es un consultant en automatisation IA.
Rédige un email de prise de contact professionnel (max {EMAIL_CHAUD_MOTS} mots) en français.
Prospect : {lead['nom']} de {lead['entreprise']}
Message reçu : {lead['message']}
""")
    return {"email_content": result.content.strip()}

def email_nurturing(state: LeadState) -> LeadState:
    """Génère un email de nurturing pour un lead tiède."""
    lead = state["lead"]
    llm = get_llm()
    result = invoke_with_retry(llm, f"""
Tu es un consultant en automatisation IA.
Rédige un email de nurturing (max {EMAIL_TIEDE_MOTS} mots) en français.
Prospect : {lead['nom']} de {lead['entreprise']}
Message : {lead['message']}
""")
    return {"email_content": result.content.strip()}

def archive_lead(state: LeadState) -> LeadState:
    """Archive les leads froids."""
    return {"email_content": "Lead archivé — score trop faible."}

def route_category(state: LeadState) -> str:
    """Fonction de routing conditionnel."""
    return state["category"]

# ── Graph factory ──────────────────────────────────────────
def build_graph():
    """Construit et compile le graphe LangGraph."""
    graph = StateGraph(LeadState)

    graph.add_node("score_lead",      score_lead)
    graph.add_node("route_lead",      route_lead)
    graph.add_node("email_contact",   email_contact)
    graph.add_node("email_nurturing", email_nurturing)
    graph.add_node("archive",         archive_lead)

    graph.add_edge(START, "score_lead")
    graph.add_edge("score_lead", "route_lead")
    graph.add_conditional_edges("route_lead", route_category, {
        "chaud": "email_contact",
        "tiede": "email_nurturing",
        "froid": "archive",
    })
    graph.add_edge("email_contact",   END)
    graph.add_edge("email_nurturing", END)
    graph.add_edge("archive",         END)

    return graph.compile()