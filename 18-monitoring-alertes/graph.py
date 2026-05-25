import time
import base64
from typing import TypedDict, Optional
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=1024,
)

# ─── State ───────────────────────────────────────────────────────────────────
class MonitoringState(TypedDict):
    # Input
    metrics:     dict   # {metric_name: value}
    thresholds:  dict   # {metric_name: threshold}
    context:     str    # contexte système (nom app, environnement...)

    # Runtime
    anomalies:   Optional[list]
    analysis:    Optional[str]
    alert_sent:  bool

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

def _get_gmail_service():
    creds = None
    if os.path.exists(config.GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.GMAIL_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def _send_email(service, to: str, subject: str, body: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = config.SENDER_EMAIL
    msg["To"]      = to
    msg.attach(MIMEText(body, "plain", "utf-8"))
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def detect_anomalies(state: MonitoringState) -> MonitoringState:
    """Détecte les métriques qui dépassent les seuils."""
    try:
        anomalies  = []
        thresholds = state["thresholds"]
        metrics    = state["metrics"]

        for metric, value in metrics.items():
            threshold = thresholds.get(metric)
            if threshold is None:
                continue

            ratio = value / threshold if threshold > 0 else 0

            if ratio >= config.ALERT_LEVELS["critical"]:
                level = "🔴 CRITIQUE"
            elif ratio >= config.ALERT_LEVELS["warning"]:
                level = "🟡 AVERTISSEMENT"
            else:
                level = "🟢 OK"

            anomalies.append({
                "metric":    metric,
                "value":     value,
                "threshold": threshold,
                "ratio":     round(ratio, 2),
                "level":     level,
            })

        # Tri par ratio décroissant
        anomalies.sort(key=lambda x: x["ratio"], reverse=True)

        has_alert = any(a["ratio"] >= 1.0 for a in anomalies)
        return {
            **state,
            "anomalies": anomalies,
            "status":    "anomalies_detected" if has_alert else "ok",
        }

    except Exception as e:
        return {**state, "errors": [f"Détection anomalies : {e}"], "status": "error"}


def analyse_anomalies(state: MonitoringState) -> MonitoringState:
    """Analyse la cause probable et génère des suggestions correctives."""
    try:
        anomalies_text = "\n".join([
            f"- {a['metric']} : {a['value']} (seuil : {a['threshold']}) → {a['level']}"
            for a in state["anomalies"]
        ])

        prompt = f"""Tu es un expert en monitoring système. Analyse ces métriques.

CONTEXTE : {state['context']}

MÉTRIQUES :
{anomalies_text}

Pour chaque anomalie détectée (niveau AVERTISSEMENT ou CRITIQUE) :
1. Cause probable
2. Impact potentiel sur le système
3. Action corrective recommandée (concrète et immédiate)

Si tout est OK, confirme-le brièvement.
Réponds en français, concis et technique.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "analysis": response.content}

    except Exception as e:
        return {**state, "errors": [f"Analyse anomalies : {e}"], "status": "error"}


def save_alert(state: MonitoringState) -> MonitoringState:
    """Enregistre l'alerte dans Supabase."""
    try:
        has_alert = any(a["ratio"] >= 1.0 for a in state["anomalies"])

        _supabase().table(config.SUPABASE_TABLE).insert({
            "context":    state["context"],
            "metrics":    str(state["metrics"]),
            "anomalies":  str(state["anomalies"]),
            "analysis":   state["analysis"],
            "has_alert":  has_alert,
            "created_at": _now(),
        }).execute()

        return {**state}

    except Exception as e:
        # Non bloquant
        return {**state, "errors": state["errors"] + [f"Supabase (non bloquant) : {e}"]}


def send_alert_email(state: MonitoringState) -> MonitoringState:
    """Envoie un email d'alerte si des anomalies critiques sont détectées."""
    try:
        critical = [a for a in state["anomalies"] if "CRITIQUE" in a["level"]]

        if not critical or not config.ALERT_EMAIL:
            return {**state, "alert_sent": False, "status": "completed"}

        service = _get_gmail_service()

        anomalies_text = "\n".join([
            f"- {a['metric']} : {a['value']} (seuil : {a['threshold']}) → {a['level']}"
            for a in critical
        ])

        body = f"""🚨 ALERTE CRITIQUE — {state['context']}

Métriques en anomalie :
{anomalies_text}

Analyse :
{state['analysis']}

---
Alerte générée automatiquement par le système de monitoring.
"""
        _send_email(
            service,
            config.ALERT_EMAIL,
            f"🚨 Alerte critique — {state['context']}",
            body,
        )

        return {**state, "alert_sent": True, "status": "completed"}

    except Exception as e:
        return {**state, "alert_sent": False, "errors": state["errors"] + [f"Email alerte : {e}"], "status": "completed"}


# ─── Router ───────────────────────────────────────────────────────────────────
def after_anomalies(state: MonitoringState) -> str:
    if state["status"] == "error":
        return END
    return "analyse_anomalies"


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(MonitoringState)

    g.add_node("detect_anomalies",  detect_anomalies)
    g.add_node("analyse_anomalies", analyse_anomalies)
    g.add_node("save_alert",        save_alert)
    g.add_node("send_alert_email",  send_alert_email)

    g.set_entry_point("detect_anomalies")

    g.add_conditional_edges("detect_anomalies",  after_anomalies)
    g.add_conditional_edges("analyse_anomalies", _stop_on_error("save_alert"))
    g.add_conditional_edges("save_alert",        _stop_on_error("send_alert_email"))
    g.add_edge("send_alert_email", END)

    return g.compile()


def run_monitoring(metrics: dict, thresholds: dict, context: str) -> MonitoringState:
    initial_state = MonitoringState(
        metrics    = metrics,
        thresholds = thresholds,
        context    = context,
        anomalies  = None,
        analysis   = None,
        alert_sent = False,
        errors     = [],
        status     = "pending",
    )
    return build_graph().invoke(initial_state)