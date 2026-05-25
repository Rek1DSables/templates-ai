import time
import requests
from typing import TypedDict, Optional
from datetime import datetime, timezone

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class LegalWatchState(TypedDict):
    # Input
    company_name:    str
    legal_domain:    str
    jurisdiction:    str
    company_context: str   # description de l'activité de l'entreprise

    # Runtime
    raw_results:     Optional[list]
    legal_updates:   Optional[list]
    impact_analysis: Optional[str]
    action_plan:     Optional[str]
    watch_id:        Optional[str]

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

def _supabase():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

def _search(query: str, n: int = 5) -> list:
    """Recherche via Serper."""
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": query, "gl": "fr", "hl": "fr", "num": n},
            timeout=10,
        )
        response.raise_for_status()
        return response.json().get("organic", [])
    except:
        return []

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def search_legal_updates(state: LegalWatchState) -> LegalWatchState:
    """Recherche les actualités juridiques récentes."""
    try:
        domain       = state["legal_domain"]
        jurisdiction = state["jurisdiction"]

        queries = [
            f"{domain} {jurisdiction} nouvelles obligations 2025 2026",
            f"{domain} {jurisdiction} réglementation mise à jour récente",
            f"{domain} entreprise conformité sanctions 2026",
        ]

        all_results = []
        for query in queries:
            results = _search(query, n=4)
            all_results.extend(results)

        if not all_results:
            return {**state, "errors": ["Aucun résultat trouvé."], "status": "error"}

        return {**state, "raw_results": all_results, "status": "searched"}

    except Exception as e:
        return {**state, "errors": [f"Recherche : {e}"], "status": "error"}


def extract_legal_updates(state: LegalWatchState) -> LegalWatchState:
    """Extrait et structure les mises à jour juridiques pertinentes."""
    try:
        results_text = "\n".join([
            f"- {r.get('title', '')} : {r.get('snippet', '')}"
            for r in state["raw_results"][:12]
        ])

        prompt = f"""Tu es un juriste expert. Analyse ces résultats de recherche et extrais les mises à jour juridiques pertinentes.

DOMAINE : {state['legal_domain']}
JURIDICTION : {state['jurisdiction']}

RÉSULTATS DE RECHERCHE :
{results_text}

Extrais et structure les 5 mises à jour les plus importantes :
Pour chaque mise à jour :
1. Titre court
2. Description (2-3 phrases)
3. Date d'application (si mentionnée)
4. Niveau d'urgence : 🔴 Urgent | 🟡 Important | 🟢 À surveiller
5. Source probable

Réponds en français, format structuré.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        # Structuration simple
        legal_updates = [{"content": response.content}]

        return {**state, "legal_updates": legal_updates, "status": "extracted"}

    except Exception as e:
        return {**state, "errors": [f"Extraction : {e}"], "status": "error"}


def analyse_impact(state: LegalWatchState) -> LegalWatchState:
    """Analyse l'impact sur l'entreprise."""
    try:
        updates_text = state["legal_updates"][0]["content"]

        prompt = f"""Tu es un juriste conseil. Analyse l'impact de ces évolutions réglementaires sur cette entreprise.

ENTREPRISE : {state['company_name']}
ACTIVITÉ : {state['company_context']}
DOMAINE JURIDIQUE : {state['legal_domain']}

ÉVOLUTIONS RÉGLEMENTAIRES :
{updates_text}

Analyse :
1. Impact direct sur l'activité (fort / modéré / faible)
2. Obligations spécifiques qui s'appliquent à cette entreprise
3. Risques de non-conformité (sanctions potentielles)
4. Délais de mise en conformité
5. Ressources nécessaires (juridique, technique, financière)

Français, concis, orienté conformité.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "impact_analysis": response.content, "status": "analysed"}

    except Exception as e:
        return {**state, "errors": [f"Analyse impact : {e}"], "status": "error"}


def generate_action_plan(state: LegalWatchState) -> LegalWatchState:
    """Génère un plan d'action de mise en conformité."""
    try:
        prompt = f"""Tu es un consultant en conformité réglementaire. Génère un plan d'action concret.

ENTREPRISE : {state['company_name']}
DOMAINE : {state['legal_domain']}

ANALYSE D'IMPACT :
{state['impact_analysis']}

Génère un plan d'action en 5 à 8 étapes :
- Chaque étape avec un délai précis
- Responsable suggéré (DPO, RH, Direction, IT...)
- Ressources nécessaires
- Critère de validation

Format : plan d'action numéroté, professionnel, actionnable immédiatement.
Français uniquement.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "action_plan": response.content, "status": "plan_generated"}

    except Exception as e:
        return {**state, "errors": [f"Plan d'action : {e}"], "status": "error"}


def save_to_supabase(state: LegalWatchState) -> LegalWatchState:
    """Enregistre la veille dans Supabase."""
    try:
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "company_name":    state["company_name"],
            "legal_domain":    state["legal_domain"],
            "jurisdiction":    state["jurisdiction"],
            "legal_updates":   state["legal_updates"][0]["content"] if state["legal_updates"] else "",
            "impact_analysis": state["impact_analysis"],
            "action_plan":     state["action_plan"],
            "created_at":      _now(),
        }).execute()

        watch_id = result.data[0]["id"]
        return {**state, "watch_id": watch_id, "status": "completed"}

    except Exception as e:
        return {**state, "status": "completed", "errors": state["errors"] + [f"Supabase (non bloquant) : {e}"]}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(LegalWatchState)

    g.add_node("search_legal_updates",  search_legal_updates)
    g.add_node("extract_legal_updates", extract_legal_updates)
    g.add_node("analyse_impact",        analyse_impact)
    g.add_node("generate_action_plan",  generate_action_plan)
    g.add_node("save_to_supabase",      save_to_supabase)

    g.set_entry_point("search_legal_updates")

    g.add_conditional_edges("search_legal_updates",  _stop_on_error("extract_legal_updates"))
    g.add_conditional_edges("extract_legal_updates", _stop_on_error("analyse_impact"))
    g.add_conditional_edges("analyse_impact",        _stop_on_error("generate_action_plan"))
    g.add_conditional_edges("generate_action_plan",  _stop_on_error("save_to_supabase"))
    g.add_edge("save_to_supabase", END)

    return g.compile()


def run_legal_watch(company_name: str, legal_domain: str, jurisdiction: str,
                    company_context: str) -> LegalWatchState:
    initial_state = LegalWatchState(
        company_name    = company_name,
        legal_domain    = legal_domain,
        jurisdiction    = jurisdiction,
        company_context = company_context,
        raw_results     = None,
        legal_updates   = None,
        impact_analysis = None,
        action_plan     = None,
        watch_id        = None,
        errors          = [],
        status          = "pending",
    )
    return build_graph().invoke(initial_state)