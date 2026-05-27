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
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class NewsletterState(TypedDict):
    # Input
    topic:       str
    tone:        str
    audience:    str
    key_points:  str

    # Runtime
    subject:     Optional[str]
    content:     Optional[str]
    subscribers: Optional[list]
    sent_count:  int

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

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def generate_subject(state: NewsletterState) -> NewsletterState:
    """Génère un objet d'email accrocheur."""
    try:
        prompt = f"""Tu es un expert en email marketing. Génère 3 objets d'email accrocheurs.

Sujet : {state['topic']}
Tonalité : {state['tone']}
Audience : {state['audience']}

Consignes :
- 3 propositions numérotées
- 50 caractères maximum par objet
- Chaque objet doit donner envie d'ouvrir l'email
- Pas d'emojis sauf si tonalité décontractée

Réponds uniquement avec les 3 objets numérotés.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        # Prend le premier objet proposé
        lines   = [l.strip() for l in response.content.strip().split("\n") if l.strip()]
        subject = lines[0].lstrip("1.").lstrip("1)").strip() if lines else state["topic"]
        return {**state, "subject": subject}

    except Exception as e:
        return {**state, "errors": [f"Génération objet : {e}"], "status": "error"}


def generate_content(state: NewsletterState) -> NewsletterState:
    """Génère le contenu complet de la newsletter."""
    try:
        prompt = f"""Tu es un expert en copywriting. Rédige une newsletter professionnelle.

Sujet : {state['topic']}
Tonalité : {state['tone']}
Audience : {state['audience']}
Points clés à aborder : {state['key_points']}
Entreprise : {config.COMPANY_NAME}

Structure :
1. Accroche (2-3 phrases percutantes)
2. Corps principal (développe les points clés)
3. Call-to-action clair
4. Signature

Consignes :
- Langue française
- Tonalité : {state['tone']}
- 300-400 mots
- Paragraphes courts et aérés
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        content  = response.content + f"\n\n---\n{config.COMPANY_NAME}\nSe désabonner : {config.UNSUBSCRIBE_URL}"
        return {**state, "content": content, "status": "generated"}

    except Exception as e:
        return {**state, "errors": [f"Génération contenu : {e}"], "status": "error"}


def fetch_subscribers(state: NewsletterState) -> NewsletterState:
    """Récupère la liste des abonnés depuis Supabase."""
    try:
        result = _supabase().table(config.SUPABASE_TABLE).select("*").eq("active", True).execute()
        subscribers = result.data

        if not subscribers:
            return {**state, "errors": ["Aucun abonné actif trouvé."], "status": "error"}

        return {**state, "subscribers": subscribers}

    except Exception as e:
        return {**state, "errors": [f"Récupération abonnés : {e}"], "status": "error"}


def send_newsletter(state: NewsletterState) -> NewsletterState:
    """Envoie la newsletter à tous les abonnés."""
    try:
        service   = _get_gmail_service()
        sent      = 0
        errors    = []

        for subscriber in state["subscribers"]:
            try:
                _send_email(service, subscriber["email"], state["subject"], state["content"])
                sent += 1
                time.sleep(0.5)  # Évite le rate limiting Gmail
            except Exception as e:
                errors.append(f"Erreur envoi {subscriber['email']} : {e}")

        return {
            **state,
            "sent_count": sent,
            "errors":     state["errors"] + errors,
            "status":     "completed",
        }

    except Exception as e:
        return {**state, "errors": [f"Envoi newsletter : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(NewsletterState)

    g.add_node("generate_subject",  generate_subject)
    g.add_node("generate_content",  generate_content)
    g.add_node("fetch_subscribers", fetch_subscribers)
    g.add_node("send_newsletter",   send_newsletter)

    g.set_entry_point("generate_subject")

    g.add_conditional_edges("generate_subject",  _stop_on_error("generate_content"))
    g.add_conditional_edges("generate_content",  _stop_on_error("fetch_subscribers"))
    g.add_conditional_edges("fetch_subscribers", _stop_on_error("send_newsletter"))
    g.add_edge("send_newsletter", END)

    return g.compile()


def preview_newsletter(topic: str, tone: str, audience: str, key_points: str) -> NewsletterState:
    """Génère uniquement le contenu sans envoyer."""
    initial_state = NewsletterState(
        topic=topic, tone=tone, audience=audience, key_points=key_points,
        subject=None, content=None, subscribers=None, sent_count=0,
        errors=[], status="pending",
    )
    g = StateGraph(NewsletterState)
    g.add_node("generate_subject", generate_subject)
    g.add_node("generate_content", generate_content)
    g.set_entry_point("generate_subject")
    g.add_conditional_edges("generate_subject", _stop_on_error("generate_content"))
    g.add_edge("generate_content", END)
    return g.compile().invoke(initial_state)


def run_newsletter(topic: str, tone: str, audience: str, key_points: str) -> NewsletterState:
    initial_state = NewsletterState(
        topic=topic, tone=tone, audience=audience, key_points=key_points,
        subject=None, content=None, subscribers=None, sent_count=0,
        errors=[], status="pending",
    )
    return build_graph().invoke(initial_state)