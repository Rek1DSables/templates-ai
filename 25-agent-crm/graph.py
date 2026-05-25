import time
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
    max_tokens=1024,
)

# ─── State ───────────────────────────────────────────────────────────────────
class CRMState(TypedDict):
    # Action
    action: str  # add_contact | add_interaction | update_stage | get_pipeline | get_contact_summary

    # Contact
    contact_id:   Optional[str]
    name:         Optional[str]
    email:        Optional[str]
    company:      Optional[str]
    phone:        Optional[str]
    stage:        Optional[str]

    # Interaction
    interaction_type: Optional[str]
    interaction_note: Optional[str]

    # Opportunité
    opportunity_id: Optional[str]
    deal_value:     Optional[float]
    new_stage:      Optional[str]

    # Runtime
    contacts:     Optional[list]
    interactions: Optional[list]
    opportunities: Optional[list]
    summary:      Optional[str]
    pipeline_stats: Optional[dict]

    # Suivi
    errors: list
    status_pipeline: str

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

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def route_action(state: CRMState) -> CRMState:
    valid = ["add_contact", "add_interaction", "update_stage", "get_pipeline", "get_contact_summary"]
    if state["action"] not in valid:
        return {**state, "errors": [f"Action invalide : {state['action']}"], "status_pipeline": "error"}
    return {**state, "errors": [], "status_pipeline": "routed"}


def add_contact(state: CRMState) -> CRMState:
    """Ajoute un nouveau contact et crée une opportunité."""
    try:
        sb = _supabase()

        # Création contact
        contact = sb.table(config.CONTACTS_TABLE).insert({
            "name":       state["name"],
            "email":      state["email"],
            "company":    state["company"],
            "phone":      state.get("phone"),
            "created_at": _now(),
        }).execute()

        contact_id = contact.data[0]["id"]

        # Création opportunité associée
        sb.table(config.OPPORTUNITIES_TABLE).insert({
            "contact_id":  contact_id,
            "contact_name": state["name"],
            "company":     state["company"],
            "stage":       "Prospect",
            "deal_value":  state.get("deal_value", 0),
            "created_at":  _now(),
        }).execute()

        return {**state, "contact_id": contact_id, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Ajout contact : {e}"], "status_pipeline": "error"}


def add_interaction(state: CRMState) -> CRMState:
    """Enregistre une interaction avec un contact."""
    try:
        if not state.get("contact_id"):
            return {**state, "errors": ["ID contact requis."], "status_pipeline": "error"}

        _supabase().table(config.INTERACTIONS_TABLE).insert({
            "contact_id":       state["contact_id"],
            "interaction_type": state["interaction_type"],
            "note":             state["interaction_note"],
            "created_at":       _now(),
        }).execute()

        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Ajout interaction : {e}"], "status_pipeline": "error"}


def update_stage(state: CRMState) -> CRMState:
    """Met à jour l'étape d'une opportunité."""
    try:
        if not state.get("contact_id") or not state.get("new_stage"):
            return {**state, "errors": ["ID contact et nouvelle étape requis."], "status_pipeline": "error"}

        _supabase().table(config.OPPORTUNITIES_TABLE).update({
            "stage":      state["new_stage"],
            "updated_at": _now(),
        }).eq("contact_id", state["contact_id"]).execute()

        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Mise à jour étape : {e}"], "status_pipeline": "error"}


def get_pipeline(state: CRMState) -> CRMState:
    """Récupère le pipeline complet et génère un résumé IA."""
    try:
        sb            = _supabase()
        opportunities = sb.table(config.OPPORTUNITIES_TABLE).select("*").order("created_at", desc=False).execute().data
        contacts      = sb.table(config.CONTACTS_TABLE).select("*").execute().data

        # Stats par étape
        pipeline_stats = {}
        for stage in config.PIPELINE_STAGES:
            stage_opps = [o for o in opportunities if o["stage"] == stage]
            pipeline_stats[stage] = {
                "count": len(stage_opps),
                "value": sum(o.get("deal_value", 0) for o in stage_opps),
            }

        # Résumé IA
        opps_text = "\n".join([
            f"- {o['contact_name']} ({o['company']}) — {o['stage']} — {o.get('deal_value', 0)}€"
            for o in opportunities[:15]
        ])

        prompt = f"""Tu es un directeur commercial. Analyse ce pipeline de vente.

OPPORTUNITÉS :
{opps_text or 'Aucune opportunité'}

STATS PAR ÉTAPE :
{chr(10).join([f"- {k} : {v['count']} opportunités — {v['value']}€" for k, v in pipeline_stats.items()])}

Fournis :
1. Valeur totale du pipeline
2. Opportunités prioritaires à traiter
3. Points de blocage identifiés
4. Actions commerciales recommandées

Français, concis, orienté action.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        return {
            **state,
            "opportunities":  opportunities,
            "contacts":       contacts,
            "pipeline_stats": pipeline_stats,
            "summary":        response.content,
            "status_pipeline": "completed",
        }

    except Exception as e:
        return {**state, "errors": [f"Pipeline : {e}"], "status_pipeline": "error"}


def get_contact_summary(state: CRMState) -> CRMState:
    """Génère une fiche résumé d'un contact avec historique."""
    try:
        if not state.get("contact_id"):
            return {**state, "errors": ["ID contact requis."], "status_pipeline": "error"}

        sb           = _supabase()
        contact      = sb.table(config.CONTACTS_TABLE).select("*").eq("id", state["contact_id"]).execute().data
        interactions = sb.table(config.INTERACTIONS_TABLE).select("*").eq("contact_id", state["contact_id"]).order("created_at", desc=True).execute().data
        opportunity  = sb.table(config.OPPORTUNITIES_TABLE).select("*").eq("contact_id", state["contact_id"]).execute().data

        if not contact:
            return {**state, "errors": ["Contact introuvable."], "status_pipeline": "error"}

        c = contact[0]
        interactions_text = "\n".join([
            f"- [{i['interaction_type']}] {i['created_at'][:10]} : {i['note']}"
            for i in interactions[:10]
        ])

        prompt = f"""Tu es un commercial expert. Génère une fiche résumé de ce contact.

CONTACT :
- Nom : {c['name']}
- Entreprise : {c.get('company', '—')}
- Email : {c.get('email', '—')}
- Étape : {opportunity[0]['stage'] if opportunity else 'Prospect'}
- Valeur deal : {opportunity[0].get('deal_value', 0) if opportunity else 0}€

HISTORIQUE INTERACTIONS :
{interactions_text or 'Aucune interaction enregistrée'}

Génère :
1. Résumé de la relation commerciale
2. Prochaine action recommandée
3. Points d'attention
4. Score d'opportunité (1-10) avec justification

Français, concis, actionnable.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        return {
            **state,
            "contacts":      contact,
            "interactions":  interactions,
            "opportunities": opportunity,
            "summary":       response.content,
            "status_pipeline": "completed",
        }

    except Exception as e:
        return {**state, "errors": [f"Résumé contact : {e}"], "status_pipeline": "error"}


# ─── Router ───────────────────────────────────────────────────────────────────
def action_router(state: CRMState) -> str:
    if state["status_pipeline"] == "error":
        return END
    return state["action"]


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(CRMState)

    g.add_node("route_action",        route_action)
    g.add_node("add_contact",         add_contact)
    g.add_node("add_interaction",     add_interaction)
    g.add_node("update_stage",        update_stage)
    g.add_node("get_pipeline",        get_pipeline)
    g.add_node("get_contact_summary", get_contact_summary)

    g.set_entry_point("route_action")

    g.add_conditional_edges("route_action", action_router, {
        "add_contact":         "add_contact",
        "add_interaction":     "add_interaction",
        "update_stage":        "update_stage",
        "get_pipeline":        "get_pipeline",
        "get_contact_summary": "get_contact_summary",
        END:                    END,
    })

    g.add_edge("add_contact",         END)
    g.add_edge("add_interaction",     END)
    g.add_edge("update_stage",        END)
    g.add_edge("get_pipeline",        END)
    g.add_edge("get_contact_summary", END)

    return g.compile()


def run_action(action: str, **kwargs) -> CRMState:
    initial_state = CRMState(
        action            = action,
        contact_id        = kwargs.get("contact_id"),
        name              = kwargs.get("name"),
        email             = kwargs.get("email"),
        company           = kwargs.get("company"),
        phone             = kwargs.get("phone"),
        stage             = kwargs.get("stage"),
        interaction_type  = kwargs.get("interaction_type"),
        interaction_note  = kwargs.get("interaction_note"),
        opportunity_id    = kwargs.get("opportunity_id"),
        deal_value        = kwargs.get("deal_value"),
        new_stage         = kwargs.get("new_stage"),
        contacts          = None,
        interactions      = None,
        opportunities     = None,
        summary           = None,
        pipeline_stats    = None,
        errors            = [],
        status_pipeline   = "pending",
    )
    return build_graph().invoke(initial_state)