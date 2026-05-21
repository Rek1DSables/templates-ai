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
class ProjectState(TypedDict):
    # Action demandée
    action:      str   # add_task | update_task | delete_task | get_summary

    # Données tâche
    task_id:     Optional[str]
    task_name:   Optional[str]
    description: Optional[str]
    status:      Optional[str]
    priority:    Optional[str]
    assignee:    Optional[str]
    due_date:    Optional[str]

    # Runtime
    tasks:       Optional[list]
    summary:     Optional[str]

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

def _stop_on_error(next_node):
    def router(state):
        return END if state["status_pipeline"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def route_action(state: ProjectState) -> ProjectState:
    """Valide et route l'action demandée."""
    valid_actions = ["add_task", "update_task", "delete_task", "get_summary"]
    if state["action"] not in valid_actions:
        return {**state, "errors": [f"Action invalide : {state['action']}"], "status_pipeline": "error"}
    return {**state, "errors": [], "status_pipeline": "routed"}

def add_task(state: ProjectState) -> ProjectState:
    """Ajoute une nouvelle tâche dans Supabase."""
    try:
        if not state.get("task_name"):
            return {**state, "errors": ["Nom de tâche requis."], "status_pipeline": "error"}

        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "task_name":   state["task_name"],
            "description": state.get("description", ""),
            "status":      state.get("status", "À faire"),
            "priority":    state.get("priority", "Moyenne"),
            "assignee":    state.get("assignee", ""),
            "due_date":    state.get("due_date"),
            "created_at":  _now(),
        }).execute()

        return {**state, "task_id": result.data[0]["id"], "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Ajout tâche : {e}"], "status_pipeline": "error"}


def update_task(state: ProjectState) -> ProjectState:
    """Met à jour une tâche existante."""
    try:
        if not state.get("task_id"):
            return {**state, "errors": ["ID de tâche requis."], "status_pipeline": "error"}

        updates = {}
        if state.get("status"):      updates["status"]      = state["status"]
        if state.get("priority"):    updates["priority"]    = state["priority"]
        if state.get("assignee"):    updates["assignee"]    = state["assignee"]
        if state.get("description"): updates["description"] = state["description"]
        if state.get("due_date"):    updates["due_date"]    = state["due_date"]
        updates["updated_at"] = _now()

        _supabase().table(config.SUPABASE_TABLE).update(updates).eq("id", state["task_id"]).execute()
        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Mise à jour tâche : {e}"], "status_pipeline": "error"}


def delete_task(state: ProjectState) -> ProjectState:
    """Supprime une tâche."""
    try:
        if not state.get("task_id"):
            return {**state, "errors": ["ID de tâche requis."], "status_pipeline": "error"}

        _supabase().table(config.SUPABASE_TABLE).delete().eq("id", state["task_id"]).execute()
        return {**state, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Suppression tâche : {e}"], "status_pipeline": "error"}


def get_summary(state: ProjectState) -> ProjectState:
    """Récupère toutes les tâches et génère un résumé IA."""
    try:
        result = _supabase().table(config.SUPABASE_TABLE).select("*").order("created_at", desc=False).execute()
        tasks  = result.data

        if not tasks:
            return {**state, "tasks": [], "summary": "Aucune tâche en cours.", "status_pipeline": "completed"}

        # Résumé IA
        tasks_text = "\n".join([
            f"- [{t['status']}] {t['task_name']} | Priorité : {t['priority']} | Assigné : {t.get('assignee', 'Non assigné')} | Échéance : {t.get('due_date', 'Non définie')}"
            for t in tasks
        ])

        prompt = f"""Tu es un chef de projet. Analyse cet état des tâches et génère un résumé exécutif.

TÂCHES :
{tasks_text}

Fournis :
1. Avancement global (% estimé)
2. Points d'attention (tâches bloquées ou en retard)
3. Prochaines actions prioritaires
4. Recommandation générale

Réponds en français, concis et professionnel.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "tasks": tasks, "summary": response.content, "status_pipeline": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Récupération tâches : {e}"], "status_pipeline": "error"}


# ─── Router action ────────────────────────────────────────────────────────────
def action_router(state: ProjectState) -> str:
    if state["status_pipeline"] == "error":
        return END
    return state["action"]


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(ProjectState)

    g.add_node("route_action", route_action)
    g.add_node("add_task",     add_task)
    g.add_node("update_task",  update_task)
    g.add_node("delete_task",  delete_task)
    g.add_node("get_summary",  get_summary)

    g.set_entry_point("route_action")

    g.add_conditional_edges("route_action", action_router, {
        "add_task":    "add_task",
        "update_task": "update_task",
        "delete_task": "delete_task",
        "get_summary": "get_summary",
        END:            END,
    })

    g.add_edge("add_task",    END)
    g.add_edge("update_task", END)
    g.add_edge("delete_task", END)
    g.add_edge("get_summary", END)

    return g.compile()


def run_action(action: str, **kwargs) -> ProjectState:
    initial_state = ProjectState(
        action      = action,
        task_id     = kwargs.get("task_id"),
        task_name   = kwargs.get("task_name"),
        description = kwargs.get("description"),
        status      = kwargs.get("status"),
        priority    = kwargs.get("priority"),
        assignee    = kwargs.get("assignee"),
        due_date    = kwargs.get("due_date"),
        tasks       = None,
        summary     = None,
        errors      = [],
        status_pipeline = "pending",
    )
    return build_graph().invoke(initial_state)