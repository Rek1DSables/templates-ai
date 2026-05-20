import os
import time
import base64
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=1024,
)

# ─── State ───────────────────────────────────────────────────────────────────
class OnboardingState(TypedDict):
    client_name:         str
    client_email:        str
    client_company:      str
    client_sector:       str
    project_description: str
    client_id:             Optional[str]
    welcome_email_content: Optional[str]
    questionnaire_content: Optional[str]
    validation_ok:      bool
    db_saved:           bool
    welcome_sent:       bool
    questionnaire_sent: bool
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

def _get_gmail_service():
    creds = None
    if os.path.exists(config.GMAIL_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(
            config.GMAIL_TOKEN_FILE, config.GMAIL_SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                config.GMAIL_CREDENTIALS_FILE, config.GMAIL_SCOPES
            )
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

def _supabase():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def validate_input(state):
    errors = []
    if not state["client_name"].strip():
        errors.append("Nom client requis.")
    if not state["client_email"].strip() or "@" not in state["client_email"]:
        errors.append("Email invalide ou manquant.")
    if not state["project_description"].strip():
        errors.append("Description du projet requise.")
    if errors:
        return {**state, "validation_ok": False, "errors": errors, "status": "error"}
    return {**state, "validation_ok": True, "errors": [], "status": "pending"}

def save_to_supabase(state):
    try:
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "name":                state["client_name"],
            "email":               state["client_email"],
            "company":             state["client_company"],
            "sector":              state["client_sector"],
            "project_description": state["project_description"],
            "status":              "pending",
        }).execute()
        client_id = result.data[0]["id"]
        return {**state, "client_id": client_id, "db_saved": True, "status": "saved"}
    except Exception as e:
        return {**state, "db_saved": False, "errors": state["errors"] + [f"Supabase (save) : {e}"], "status": "error"}

def generate_welcome_email(state):
    try:
        prompt = f"""Tu rédiges un email de bienvenue professionnel et chaleureux.
Client : {state['client_name']}
Entreprise : {state['client_company'] or 'non renseignée'}
Secteur : {state['client_sector']}
Projet : {state['project_description']}

Consignes :
- En français, ton professionnel mais accessible
- Commence par "Bonjour {state['client_name'].split()[0]},"
- Confirme la prise en charge du projet
- Annonce l'arrivée d'un questionnaire de démarrage
- 150 mots maximum
- Pas de ligne "Objet :"
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "welcome_email_content": response.content + config.COMPANY_SIGNATURE}
    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Génération email bienvenue : {e}"], "status": "error"}

def send_welcome_email(state):
    try:
        service = _get_gmail_service()
        _send_email(service, state["client_email"], f"Bienvenue chez {config.COMPANY_NAME} 👋", state["welcome_email_content"])
        _supabase().table(config.SUPABASE_TABLE).update({"status": "welcome_sent", "welcome_sent_at": _now()}).eq("id", state["client_id"]).execute()
        return {**state, "welcome_sent": True, "status": "welcome_sent"}
    except Exception as e:
        return {**state, "welcome_sent": False, "errors": state["errors"] + [f"Envoi email bienvenue : {e}"], "status": "error"}

def generate_questionnaire(state):
    try:
        prompt = f"""Tu rédiges un questionnaire d'onboarding professionnel.
Client : {state['client_name']}
Secteur : {state['client_sector']}
Projet : {state['project_description']}

Consignes :
- 6 à 8 questions numérotées, ouvertes
- Couvre : objectifs, contraintes, données disponibles, KPIs, délais, parties prenantes
- Phrase d'intro et phrase de clôture courtes
- Français, ton professionnel
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "questionnaire_content": response.content + config.COMPANY_SIGNATURE}
    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Génération questionnaire : {e}"], "status": "error"}

def send_questionnaire(state):
    try:
        service = _get_gmail_service()
        _send_email(service, state["client_email"], f"[{config.COMPANY_NAME}] Questionnaire de démarrage", state["questionnaire_content"])
        _supabase().table(config.SUPABASE_TABLE).update({"status": "questionnaire_sent", "questionnaire_sent_at": _now()}).eq("id", state["client_id"]).execute()
        return {**state, "questionnaire_sent": True, "status": "questionnaire_sent"}
    except Exception as e:
        return {**state, "questionnaire_sent": False, "errors": state["errors"] + [f"Envoi questionnaire : {e}"], "status": "error"}

def finalize_onboarding(state):
    try:
        _supabase().table(config.SUPABASE_TABLE).update({"status": "completed"}).eq("id", state["client_id"]).execute()
        return {**state, "status": "completed"}
    except Exception as e:
        return {**state, "status": "completed", "errors": state["errors"] + [f"Finalisation (non bloquant) : {e}"]}

# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(OnboardingState)

    g.add_node("validate_input",         validate_input)
    g.add_node("save_to_supabase",       save_to_supabase)
    g.add_node("generate_welcome_email", generate_welcome_email)
    g.add_node("send_welcome_email",     send_welcome_email)
    g.add_node("generate_questionnaire", generate_questionnaire)
    g.add_node("send_questionnaire",     send_questionnaire)
    g.add_node("finalize_onboarding",    finalize_onboarding)

    g.set_entry_point("validate_input")

    g.add_conditional_edges("validate_input",         lambda s: "save_to_supabase" if s["validation_ok"] else END)
    g.add_conditional_edges("save_to_supabase",       _stop_on_error("generate_welcome_email"))
    g.add_conditional_edges("generate_welcome_email", _stop_on_error("send_welcome_email"))
    g.add_conditional_edges("send_welcome_email",     _stop_on_error("generate_questionnaire"))
    g.add_conditional_edges("generate_questionnaire", _stop_on_error("send_questionnaire"))
    g.add_conditional_edges("send_questionnaire",     _stop_on_error("finalize_onboarding"))
    g.add_edge("finalize_onboarding", END)

    return g.compile()

def run_onboarding(client_data: dict) -> OnboardingState:
    initial_state = OnboardingState(
        client_name         = client_data.get("name", ""),
        client_email        = client_data.get("email", ""),
        client_company      = client_data.get("company", ""),
        client_sector       = client_data.get("sector", ""),
        project_description = client_data.get("project_description", ""),
        client_id             = None,
        welcome_email_content = None,
        questionnaire_content = None,
        validation_ok      = False,
        db_saved           = False,
        welcome_sent       = False,
        questionnaire_sent = False,
        errors = [],
        status = "pending",
    )
    return build_graph().invoke(initial_state)