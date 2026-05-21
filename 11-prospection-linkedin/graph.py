import time
from typing import TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class ProspectionState(TypedDict):
    # Input
    profiles:       list   # liste de dicts {name, company, position, summary}
    offer_context:  str
    sender_name:    str
    sender_company: str

    # Runtime
    scored_profiles: Optional[list]
    messages:        Optional[list]

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

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def validate_input(state: ProspectionState) -> ProspectionState:
    errors = []
    if not state["profiles"]:
        errors.append("Au moins un profil est requis.")
    if not state["offer_context"].strip():
        errors.append("Le contexte de l'offre est requis.")
    if not state["sender_name"].strip():
        errors.append("Le nom de l'expéditeur est requis.")
    if errors:
        return {**state, "errors": errors, "status": "error"}
    return {**state, "errors": [], "status": "pending"}


def score_profiles(state: ProspectionState) -> ProspectionState:
    """Score chaque profil selon sa pertinence avec l'offre."""
    try:
        scored = []
        for profile in state["profiles"]:
            prompt = f"""Tu es un expert en prospection B2B. Évalue la pertinence de ce profil.

OFFRE PROPOSÉE :
{state['offer_context']}

PROFIL :
- Nom : {profile.get('name', '')}
- Titre : {profile.get('position', '')}
- Entreprise : {profile.get('company', '')}
- Résumé : {profile.get('summary', 'Non renseigné')}

Réponds UNIQUEMENT avec ce format JSON :
{{
  "score": <nombre entre 1 et 10>,
  "raison": "<explication courte en 1 phrase>",
  "priorite": "<Haute | Moyenne | Faible>"
}}
"""
            response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

            import json, re
            json_match = re.search(r'\{.*?\}', response.content, re.DOTALL)
            if json_match:
                scoring = json.loads(json_match.group())
            else:
                scoring = {"score": 5, "raison": "Analyse non disponible", "priorite": "Moyenne"}

            scored.append({**profile, **scoring})

        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        return {**state, "scored_profiles": scored, "status": "scored"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Scoring profils : {e}"], "status": "error"}


def draft_messages(state: ProspectionState) -> ProspectionState:
    """Rédige un message personnalisé pour chaque profil score >= 6."""
    try:
        messages = []
        top_profiles = [p for p in state["scored_profiles"] if p.get("score", 0) >= 6]

        for profile in top_profiles:
            prompt = f"""Tu rédiges un message de prospection LinkedIn court et personnalisé.

EXPÉDITEUR :
- Nom : {state['sender_name']}
- Entreprise : {state['sender_company']}

OFFRE :
{state['offer_context']}

PROFIL CIBLE :
- Nom : {profile.get('name', '')}
- Titre : {profile.get('position', '')}
- Entreprise : {profile.get('company', '')}
- Résumé : {profile.get('summary', 'Non renseigné')[:300]}

Consignes :
- 80 mots maximum
- Accroche personnalisée basée sur le profil
- Valeur ajoutée claire en 1 phrase
- Call-to-action simple
- Ton professionnel et direct
- Ne pas commencer par "Bonjour,"
"""
            response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
            messages.append({
                "name":     profile.get("name", ""),
                "company":  profile.get("company", ""),
                "score":    profile.get("score", 0),
                "priorite": profile.get("priorite", ""),
                "raison":   profile.get("raison", ""),
                "message":  response.content,
            })

        return {**state, "messages": messages, "status": "completed"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Rédaction messages : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(ProspectionState)

    g.add_node("validate_input",  validate_input)
    g.add_node("score_profiles",  score_profiles)
    g.add_node("draft_messages",  draft_messages)

    g.set_entry_point("validate_input")

    g.add_conditional_edges("validate_input", _stop_on_error("score_profiles"))
    g.add_conditional_edges("score_profiles", _stop_on_error("draft_messages"))
    g.add_edge("draft_messages", END)

    return g.compile()


def run_prospection(profiles: list, offer_context: str, sender_name: str, sender_company: str) -> ProspectionState:
    initial_state = ProspectionState(
        profiles       = profiles,
        offer_context  = offer_context,
        sender_name    = sender_name,
        sender_company = sender_company,
        scored_profiles = None,
        messages       = None,
        errors         = [],
        status         = "pending",
    )
    return build_graph().invoke(initial_state)