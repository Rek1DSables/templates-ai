# graph.py
import time
import json
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    SERPER_API_KEY, SERPER_URL,
    MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContentState(TypedDict):
    sujet: str
    canal: str
    ton: str
    longueur: str
    audience: str
    contexte: str
    envoyer_email: bool
    destinataire_email: str
    objet_email: str
    resultats_recherche: str
    contenu_genere: str
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


def rechercher_contexte(state: ContentState) -> ContentState:
    try:
        if not SERPER_API_KEY:
            return {**state, "resultats_recherche": "", "erreur": ""}

        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": f"{state['sujet']} {state['canal']} 2025", "num": 5}
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        data = response.json()

        resultats = []
        for item in data.get("organic", [])[:5]:
            resultats.append(f"- {item.get('title', '')} : {item.get('snippet', '')}")

        return {**state, "resultats_recherche": "\n".join(resultats), "erreur": ""}
    except Exception as e:
        return {**state, "resultats_recherche": "", "erreur": ""}


def generer_contenu(state: ContentState) -> ContentState:
    try:
        system = """Tu es un expert en creation de contenu marketing digital.
Tu crees du contenu engageant, optimise et adapte a chaque canal.
Tu reponds toujours en francais avec le style demande.
Tu termines TOUJOURS ton contenu avant de t'arreter."""

        contexte_recherche = ""
        if state["resultats_recherche"]:
            contexte_recherche = f"\nTENDANCES ACTUELLES :\n{state['resultats_recherche']}\n"

        longueur_mots = state.get("longueur", "Moyen (300-600 mots)")

        prompt = f"""Cree du contenu pour le canal suivant :

CANAL : {state['canal']}
SUJET : {state['sujet']}
TON : {state['ton']}
LONGUEUR : {longueur_mots}
AUDIENCE CIBLE : {state['audience']}
CONTEXTE SUPPLEMENTAIRE : {state['contexte']}
{contexte_recherche}

Instructions specifiques par canal :
- Article de blog : titre accrocheur + introduction + sections avec sous-titres + conclusion + CTA
- Post LinkedIn : hook puissant + contenu structuré + hashtags pertinents + question d'engagement
- Thread Twitter/X : serie de tweets numerotes, chaque tweet < 280 caracteres
- Newsletter : objet email + pre-header + corps structuré + CTA + signature
- Email marketing : objet + pre-header + corps persuasif + CTA clair
- Script YouTube : intro accrocheuse + plan + transitions + outro + CTA
- Carrousel Instagram : titre slide 1 + contenu de chaque slide + slide CTA final

Genere le contenu complet et termine le avant de t'arreter."""

        contenu = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            model=MODEL_SONNET,
        )

        return {**state, "contenu_genere": contenu, "erreur": ""}
    except Exception as e:
        return {**state, "contenu_genere": "", "erreur": f"Erreur generation : {str(e)}"}


def envoyer_newsletter(state: ContentState) -> ContentState:
    try:
        if not state["envoyer_email"] or not state["destinataire_email"]:
            return {**state, "erreur": ""}

        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        import base64
        from email.mime.text import MIMEText
        import os
        from config import GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_SCOPES

        creds = None
        if os.path.exists(GMAIL_TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_FILE, GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                from google.auth.transport.requests import Request
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(GMAIL_CREDENTIALS_FILE, GMAIL_SCOPES)
                creds = flow.run_local_server(port=0)
            with open(GMAIL_TOKEN_FILE, "w") as token:
                token.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)

        message = MIMEText(state["contenu_genere"], "plain", "utf-8")
        message["to"] = state["destinataire_email"]
        message["subject"] = state["objet_email"] or f"Newsletter : {state['sujet']}"

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        return {**state, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur envoi email : {str(e)}"}


def router(state: ContentState) -> str:
    if state["envoyer_email"] and state["destinataire_email"]:
        return "envoyer"
    return "fin"


def build_graph():
    graph = StateGraph(ContentState)
    graph.add_node("rechercher_contexte", rechercher_contexte)
    graph.add_node("generer_contenu", generer_contenu)
    graph.add_node("envoyer_newsletter", envoyer_newsletter)

    graph.set_entry_point("rechercher_contexte")
    graph.add_edge("rechercher_contexte", "generer_contenu")
    graph.add_conditional_edges(
        "generer_contenu",
        router,
        {
            "envoyer": "envoyer_newsletter",
            "fin": END,
        }
    )
    graph.add_edge("envoyer_newsletter", END)

    return graph.compile()