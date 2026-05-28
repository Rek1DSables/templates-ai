# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ReportingState(TypedDict):
    entreprise: str
    secteur: str
    periode: str
    kpis: dict
    analyse_kpis: str
    tendances: list
    alertes: list
    recommandations: str
    score_sante: int
    envoyer_email: bool
    destinataire_email: str
    rapport_pdf: bool
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 2000, model: str = None) -> str:
    m = model or MODEL_NAME
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=m,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surcharge, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def analyser_kpis(state: ReportingState) -> ReportingState:
    try:
        system = """Tu es un analyste business expert en performance et KPIs.
Tu analyses des indicateurs et identifies les tendances et alertes.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "analyse": "analyse globale en 2-3 paragraphes",
  "tendances": ["tendance 1", "tendance 2", "tendance 3"],
  "alertes": ["alerte 1", "alerte 2"],
  "score_sante": 75
}"""

        kpis_str = "\n".join([f"- {k} : {v}" for k, v in state["kpis"].items()])

        prompt = f"""Analyse ces KPIs :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Periode : {state['periode']}

KPIs :
{kpis_str}

Reponds uniquement avec le JSON."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )

        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)

        return {
            **state,
            "analyse_kpis": data.get("analyse", ""),
            "tendances": data.get("tendances", []),
            "alertes": data.get("alertes", []),
            "score_sante": int(data.get("score_sante", 50)),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def generer_recommandations(state: ReportingState) -> ReportingState:
    try:
        system = """Tu es un consultant business senior.
Tu generes des recommandations concretes et actionnables.
Tu reponds toujours en francais avec un style professionnel.
Tu termines TOUJOURS toutes tes recommandations avant de t'arreter."""

        kpis_str = "\n".join([f"- {k} : {v}" for k, v in state["kpis"].items()])

        prompt = f"""Genere des recommandations strategiques pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Periode : {state['periode']}
Score de sante : {state['score_sante']}/100

KPIs :
{kpis_str}

Tendances :
{chr(10).join(f'- {t}' for t in state['tendances'])}

Alertes :
{chr(10).join(f'- {a}' for a in state['alertes'])}

Genere 5 recommandations prioritaires avec pour chacune :
- ACTION CONCRETE
- IMPACT ATTENDU
- DELAI
- RESPONSABLE
- KPI DE SUIVI"""

        recommandations = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            model=MODEL_SONNET,
        )

        return {**state, "recommandations": recommandations, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur recommandations : {str(e)}"}


def envoyer_rapport_email(state: ReportingState) -> ReportingState:
    try:
        if not state["envoyer_email"] or not state["destinataire_email"]:
            return {**state, "erreur": ""}

        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from google.auth.transport.requests import Request
        import base64
        from email.mime.text import MIMEText
        import os
        from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_SCOPES

        creds = None
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(GMAIL_TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)

        corps = f"""RAPPORT {state['periode'].upper()} — {state['entreprise']}
Score de santé : {state['score_sante']}/100

ANALYSE :
{state['analyse_kpis']}

ALERTES :
{chr(10).join(f'- {a}' for a in state['alertes'])}

RECOMMANDATIONS :
{state['recommandations']}
"""

        message = MIMEText(corps, "plain", "utf-8")
        message["to"] = state["destinataire_email"]
        message["subject"] = f"Rapport {state['periode']} — {state['entreprise']} — Score {state['score_sante']}/100"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        return {**state, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur email : {str(e)}"}


def router(state: ReportingState) -> str:
    if state["envoyer_email"] and state["destinataire_email"]:
        return "envoyer"
    return "fin"


def build_graph():
    graph = StateGraph(ReportingState)
    graph.add_node("analyser_kpis", analyser_kpis)
    graph.add_node("generer_recommandations", generer_recommandations)
    graph.add_node("envoyer_rapport_email", envoyer_rapport_email)

    graph.set_entry_point("analyser_kpis")
    graph.add_edge("analyser_kpis", "generer_recommandations")
    graph.add_conditional_edges(
        "generer_recommandations",
        router,
        {
            "envoyer": "envoyer_rapport_email",
            "fin": END,
        }
    )
    graph.add_edge("envoyer_rapport_email", END)

    return graph.compile()