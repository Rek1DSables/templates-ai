# graph.py
import time
import json
import base64
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    GMAIL_CREDENTIALS_FILE, GMAIL_TOKEN_FILE, GMAIL_SCOPES,
    MAX_RETRIES, RETRY_DELAY, NB_EMAILS_MAX
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class EmailState(TypedDict):
    emails_bruts: list
    emails_traites: list
    mode_demo: bool
    repondre_auto: bool
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 2000) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
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


def get_gmail_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from google.auth.transport.requests import Request
    import os

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

    return build("gmail", "v1", credentials=creds)


def collecter_emails(state: EmailState) -> EmailState:
    try:
        if state["mode_demo"]:
            emails_demo = [
                {
                    "id": "demo_001",
                    "expediteur": "marie.dupont@acme.com",
                    "sujet": "Problème urgent avec mon compte - impossible de me connecter",
                    "corps": "Bonjour, depuis ce matin je n'arrive plus à me connecter à votre plateforme. J'ai un message d'erreur 403. C'est bloquant pour mon équipe. Merci de traiter en urgence.",
                    "date": "2026-06-01 09:15",
                },
                {
                    "id": "demo_002",
                    "expediteur": "jean.martin@startup.fr",
                    "sujet": "Demande de démo et tarifs pour 50 utilisateurs",
                    "corps": "Bonjour, nous sommes une startup de 50 personnes et nous cherchons une solution d'automatisation IA. Pourriez-vous nous envoyer vos tarifs et organiser une démonstration la semaine prochaine ?",
                    "date": "2026-06-01 10:30",
                },
                {
                    "id": "demo_003",
                    "expediteur": "contact@investpartners.com",
                    "sujet": "Opportunité de partenariat stratégique",
                    "corps": "Bonjour, nous représentons un fonds d'investissement spécialisé dans les solutions IA B2B. Votre solution nous intéresse pour un partenariat de distribution. Disponible pour un appel cette semaine ?",
                    "date": "2026-06-01 11:00",
                },
                {
                    "id": "demo_004",
                    "expediteur": "reclamation@client-mécontent.fr",
                    "sujet": "RÉCLAMATION FORMELLE - Facturation incorrecte",
                    "corps": "Bonjour, j'ai été facturé deux fois le mois dernier pour un montant total de 800 EUR. Je demande le remboursement immédiat et des explications. Si ce n'est pas réglé sous 48h je contacte ma banque.",
                    "date": "2026-06-01 11:45",
                },
                {
                    "id": "demo_005",
                    "expediteur": "noreply@newsletter-promo.com",
                    "sujet": "🎉 Offre spéciale - 70% de réduction aujourd'hui seulement!!!",
                    "corps": "Cliquez ici pour profiter de notre offre exceptionnelle. Produits premium à prix cassés. Livraison gratuite. Offre valable 24h seulement.",
                    "date": "2026-06-01 12:00",
                },
            ]
            return {**state, "emails_bruts": emails_demo, "erreur": ""}

        service = get_gmail_service()
        results = service.users().messages().list(
            userId="me",
            labelIds=["INBOX"],
            q="is:unread",
            maxResults=NB_EMAILS_MAX,
        ).execute()

        messages = results.get("messages", [])
        emails = []

        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="full",
            ).execute()

            headers = msg_data["payload"].get("headers", [])
            sujet = next((h["value"] for h in headers if h["name"] == "Subject"), "Sans objet")
            expediteur = next((h["value"] for h in headers if h["name"] == "From"), "Inconnu")
            date = next((h["value"] for h in headers if h["name"] == "Date"), "")

            corps = ""
            payload = msg_data.get("payload", {})
            if payload.get("body", {}).get("data"):
                corps = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
            elif payload.get("parts"):
                for part in payload["parts"]:
                    if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                        corps = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="ignore")
                        break

            emails.append({
                "id": msg["id"],
                "expediteur": expediteur,
                "sujet": sujet,
                "corps": corps[:1000],
                "date": date,
            })

        return {**state, "emails_bruts": emails, "erreur": ""}
    except Exception as e:
        return {**state, "emails_bruts": [], "erreur": f"Erreur collecte : {str(e)}"}


def traiter_emails(state: EmailState) -> EmailState:
    try:
        emails_traites = []

        system = """Tu es un assistant expert en gestion d'emails professionnels.
Tu analyses les emails et fournis une classification et une reponse appropriee.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "categorie": "Support client",
  "priorite": "urgente",
  "sentiment": "negatif",
  "resume": "resume en 1 phrase",
  "action_recommandee": "action a prendre",
  "reponse_suggeree": "reponse complete et professionnelle"
}"""

        for email in state["emails_bruts"]:
            prompt = f"""Analyse cet email et genere une reponse professionnelle :

DE : {email['expediteur']}
SUJET : {email['sujet']}
DATE : {email['date']}
CORPS :
{email['corps'][:800]}

Categories possibles : Support client, Demande commerciale, Reclamation, Partenariat, Candidature, Spam, Autre
Priorites possibles : urgente, haute, normale, basse
Sentiments possibles : positif, neutre, negatif

Reponds uniquement avec le JSON."""

            reponse = invoke_with_retry(
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
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
                    "categorie": "Autre",
                    "priorite": "normale",
                    "sentiment": "neutre",
                    "resume": "Analyse indisponible",
                    "action_recommandee": "Traitement manuel requis",
                    "reponse_suggeree": "",
                }

            emails_traites.append({
                **email,
                **data,
            })

        return {**state, "emails_traites": emails_traites, "erreur": ""}
    except Exception as e:
        return {**state, "emails_traites": [], "erreur": f"Erreur traitement : {str(e)}"}


def envoyer_reponses(state: EmailState) -> EmailState:
    try:
        if not state["repondre_auto"] or state["mode_demo"]:
            return {**state, "erreur": ""}

        service = get_gmail_service()

        for email in state["emails_traites"]:
            if email.get("categorie") == "Spam":
                continue
            if not email.get("reponse_suggeree"):
                continue

            from email.mime.text import MIMEText
            message = MIMEText(email["reponse_suggeree"], "plain", "utf-8")
            message["to"] = email["expediteur"]
            message["subject"] = f"Re: {email['sujet']}"

            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            service.users().messages().send(
                userId="me",
                body={"raw": raw},
            ).execute()

        return {**state, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur envoi : {str(e)}"}


def router(state: EmailState) -> str:
    if state["repondre_auto"] and not state["mode_demo"]:
        return "envoyer"
    return "fin"


def build_graph():
    graph = StateGraph(EmailState)
    graph.add_node("collecter_emails", collecter_emails)
    graph.add_node("traiter_emails", traiter_emails)
    graph.add_node("envoyer_reponses", envoyer_reponses)

    graph.set_entry_point("collecter_emails")
    graph.add_edge("collecter_emails", "traiter_emails")
    graph.add_conditional_edges(
        "traiter_emails",
        router,
        {
            "envoyer": "envoyer_reponses",
            "fin": END,
        }
    )
    graph.add_edge("envoyer_reponses", END)

    return graph.compile()