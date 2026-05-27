import time
import io
from typing import TypedDict, Optional
from datetime import datetime, timezone

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client
import fitz  # PyMuPDF

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class RecruitmentState(TypedDict):
    # Action
    action: str  # analyze_cv | update_status | get_pipeline

    # Input candidat
    candidate_id:   Optional[str]
    cv_bytes:       Optional[bytes]
    cv_name:        Optional[str]
    job_description: Optional[str]
    new_status:     Optional[str]

    # Runtime
    cv_text:        Optional[str]
    candidate_data: Optional[dict]
    candidates:     Optional[list]
    pipeline_summary: Optional[str]

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
def route_action(state: RecruitmentState) -> RecruitmentState:
    valid = ["analyze_cv", "update_status", "get_pipeline"]
    if state["action"] not in valid:
        return {**state, "errors": [f"Action invalide : {state['action']}"], "status_pipeline": "error"}
    return {**state, "errors": [], "status_pipeline": "routed"}


def extract_cv_text(state: RecruitmentState) -> RecruitmentState:
    """Extrait le texte du CV PDF."""
    try:
        doc  = fitz.open(stream=state["cv_bytes"], filetype="pdf")
        text = "".join([page.get_text() for page in doc])
        if not text.strip():
            return {**state, "errors": ["CV vide ou illisible."], "status_pipeline": "error"}
        return {**state, "cv_text": text}
    except Exception as e:
        return {**state, "errors": [f"Extraction CV : {e}"], "status_pipeline": "error"}


def analyze_cv(state: RecruitmentState) -> RecruitmentState:
    """Analyse le CV et score le candidat par rapport à la fiche de poste."""
    try:
        prompt = f"""Tu es un expert RH. Analyse ce CV par rapport à la fiche de poste.

FICHE DE POSTE :
{state['job_description']}

CV :
{state['cv_text'][:3000]}

Fournis une analyse structurée :
1. Nom et prénom du candidat (extrait du CV)
2. Poste actuel / dernière expérience
3. Années d'expérience estimées
4. Compétences clés identifiées
5. Score de compatibilité (1-10) avec justification
6. Points forts (3 max)
7. Points faibles ou manques (3 max)
8. Recommandation : Présélectionner | Refuser | À étudier

Réponds en français, format structuré et professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        analysis = response.content

        # Extraction du nom via LLM
        name_prompt = f"Extrait uniquement le nom complet du candidat depuis ce CV. Réponds avec juste le nom, rien d'autre.\n\n{state['cv_text'][:500]}"
        name_response = invoke_with_retry(llm, [HumanMessage(content=name_prompt)])
        candidate_name = name_response.content.strip()

        # Sauvegarde dans Supabase
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "name":             candidate_name,
            "cv_name":          state["cv_name"],
            "job_description":  state["job_description"],
            "analysis":         analysis,
            "status":           "Nouveau",
            "created_at":       _now(),
        }).execute()

        candidate_id = result.data[0]["id"]
        return {
            **state,
            "candidate_data": {
                "id":       candidate_id,
                "name":     candidate_name,
                "analysis": analysis,
                "status":   "Nouveau",
            },
            "status_pipeline": "completed"
        }

    except Exception as e:
        return {**state, "errors": [f"Analyse CV : {e}"], "status_pipeline": "error"}


def update_status(state: RecruitmentState) -> RecruitmentState:
    """Met à jour le statut d'un candidat."""
    try:
        if not state.get("candidate_id") or not state.get("new_status"):
            return {**state, "errors": ["ID candidat et nouveau statut requis."], "status_pipeline": "error"}

        _supabase().table(config.SUPABASE_TABLE).update({
            "status":     state["new_status"],
            "updated_at": _now(),
        }).eq("id", state["candidate_id"]).execute()

        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Mise à jour statut : {e}"], "status_pipeline": "error"}


def get_pipeline(state: RecruitmentState) -> RecruitmentState:
    """Récupère tous les candidats et génère un résumé du pipeline."""
    try:
        result     = _supabase().table(config.SUPABASE_TABLE).select("*").order("created_at", desc=False).execute()
        candidates = result.data

        if not candidates:
            return {**state, "candidates": [], "pipeline_summary": "Aucun candidat dans le pipeline.", "status_pipeline": "completed"}

        candidates_text = "\n".join([
            f"- {c['name']} | Statut : {c['status']} | CV : {c['cv_name']}"
            for c in candidates
        ])

        prompt = f"""Tu es un DRH. Analyse ce pipeline de recrutement et génère un résumé.

CANDIDATS :
{candidates_text}

Fournis :
1. Vue d'ensemble du pipeline (nombre par statut)
2. Candidats à prioriser
3. Prochaines actions recommandées
4. Risques identifiés (ex: pipeline vide, trop de refus)

Réponds en français, concis et professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "candidates": candidates, "pipeline_summary": response.content, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Récupération pipeline : {e}"], "status_pipeline": "error"}


# ─── Router ───────────────────────────────────────────────────────────────────
def action_router(state: RecruitmentState) -> str:
    if state["status_pipeline"] == "error":
        return END
    return state["action"]

def cv_error_router(state: RecruitmentState) -> str:
    return END if state["status_pipeline"] == "error" else "analyze_cv"

# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(RecruitmentState)

    g.add_node("route_action",    route_action)
    g.add_node("extract_cv_text", extract_cv_text)
    g.add_node("analyze_cv",      analyze_cv)
    g.add_node("update_status",   update_status)
    g.add_node("get_pipeline",    get_pipeline)

    g.set_entry_point("route_action")

    g.add_conditional_edges("route_action", action_router, {
        "analyze_cv":   "extract_cv_text",
        "update_status": "update_status",
        "get_pipeline":  "get_pipeline",
        END:             END,
    })

    g.add_conditional_edges("extract_cv_text", cv_error_router)
    g.add_edge("analyze_cv",    END)
    g.add_edge("update_status", END)
    g.add_edge("get_pipeline",  END)

    return g.compile()


def run_action(action: str, **kwargs) -> RecruitmentState:
    initial_state = RecruitmentState(
        action           = action,
        candidate_id     = kwargs.get("candidate_id"),
        cv_bytes         = kwargs.get("cv_bytes"),
        cv_name          = kwargs.get("cv_name"),
        job_description  = kwargs.get("job_description"),
        new_status       = kwargs.get("new_status"),
        cv_text          = None,
        candidate_data   = None,
        candidates       = None,
        pipeline_summary = None,
        errors           = [],
        status_pipeline  = "pending",
    )
    return build_graph().invoke(initial_state)