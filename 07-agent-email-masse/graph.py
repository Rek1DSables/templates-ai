# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY, DELAI_ENTRE_ENVOIS
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class EmailMasseState(TypedDict):
    contacts: list
    objectif: str
    ton: str
    contexte_produit: str
    expediteur_nom: str
    emails_generes: list
    emails_envoyes: int
    emails_erreurs: int
    envoyer: bool
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


def generer_emails(state: EmailMasseState) -> EmailMasseState:
    try:
        emails_generes = []

        system = f"""Tu es un expert en copywriting et email marketing B2B.
Tu rediges des emails ultra-personnalises qui obtiennent des taux de reponse eleves.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{{
  "objet": "objet de l email",
  "corps": "corps complet de l email avec salutation et signature"
}}
L email doit etre court (150-200 mots max), percutant et personnalise."""

        for contact in state["contacts"]:
            prompt = f"""Redige un email personnalise pour ce contact :

CONTACT :
- Nom : {contact.get('nom', '')}
- Prenom : {contact.get('prenom', '')}
- Entreprise : {contact.get('entreprise', '')}
- Poste : {contact.get('poste', '')}
- Secteur : {contact.get('secteur', '')}
- Info personnalisee : {contact.get('info_perso', '')}

PARAMETRES :
- Objectif : {state['objectif']}
- Ton : {state['ton']}
- Expediteur : {state['expediteur_nom']}
- Contexte produit : {state['contexte_produit']}

Reponds uniquement avec le JSON."""

            reponse = invoke_with_retry(
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
                model=MODEL_SONNET,
            )

            reponse_clean = reponse.strip()
            if reponse_clean.startswith("```"):
                reponse_clean = reponse_clean.split("```")[1]
                if reponse_clean.startswith("json"):
                    reponse_clean = reponse_clean[4:]
            reponse_clean = reponse_clean.strip()

            try:
                data = json.loads(reponse_clean)
            except Exception:
                data = {
                    "objet": f"Question rapide — {contact.get('entreprise', '')}",
                    "corps": f"Bonjour {contact.get('prenom', '')},\n\n{state['contexte_produit']}\n\nCordialement,\n{state['expediteur_nom']}",
                }

            emails_generes.append({
                **contact,
                "objet": data.get("objet", ""),
                "corps": data.get("corps", ""),
                "statut": "genere",
            })

        return {**state, "emails_generes": emails_generes, "erreur": ""}
    except Exception as e:
        return {**state, "emails_generes": [], "erreur": f"Erreur generation : {str(e)}"}


def envoyer_emails(state: EmailMasseState) -> EmailMasseState:
    try:
        if not state["envoyer"]:
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

        envoyes = 0
        erreurs = 0

        for email in state["emails_generes"]:
            try:
                if not email.get("email"):
                    continue

                message = MIMEText(email["corps"], "plain", "utf-8")
                message["to"] = email["email"]
                message["subject"] = email["objet"]

                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                service.users().messages().send(userId="me", body={"raw": raw}).execute()
                email["statut"] = "envoye"
                envoyes += 1
                time.sleep(DELAI_ENTRE_ENVOIS)
            except Exception as e:
                email["statut"] = f"erreur : {str(e)}"
                erreurs += 1

        return {
            **state,
            "emails_generes": state["emails_generes"],
            "emails_envoyes": envoyes,
            "emails_erreurs": erreurs,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur envoi : {str(e)}"}


def router(state: EmailMasseState) -> str:
    if state["envoyer"]:
        return "envoyer"
    return "fin"


def build_graph():
    graph = StateGraph(EmailMasseState)
    graph.add_node("generer_emails", generer_emails)
    graph.add_node("envoyer_emails", envoyer_emails)

    graph.set_entry_point("generer_emails")
    graph.add_conditional_edges(
        "generer_emails",
        router,
        {
            "envoyer": "envoyer_emails",
            "fin": END,
        }
    )
    graph.add_edge("envoyer_emails", END)

    return graph.compile()