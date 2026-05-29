# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY, EQUIPES, PRIORITES
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class WorkflowState(TypedDict):
    email_expediteur: str
    email_sujet: str
    email_corps: str
    email_date: str
    mode_demo: bool
    contact_connu: bool
    contact_data: dict
    historique_interactions: list
    categorie: str
    priorite: str
    sentiment: str
    resume: str
    entites_extraites: dict
    ticket_reference: str
    equipe_assignee: str
    sla_heures: int
    reponse_generee: str
    relance_programmee: str
    actions_executees: list
    audit_log: list
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 1000, model: str = None) -> str:
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
                time.sleep(RETRY_DELAY)
            else:
                raise


def log(audit_log: list, etape: str, agent: str, detail: str = "") -> list:
    audit_log.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "etape": etape,
        "agent": agent,
        "detail": detail,
    })
    return audit_log


def agent_crm_lookup(state: WorkflowState) -> WorkflowState:
    try:
        audit_log = log(state.get("audit_log", []), "Recherche CRM", "Agent CRM", f"Lookup : {state['email_expediteur']}")

        contact_data = {}
        historique = []
        contact_connu = False

        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            res = supabase.table("crm_contacts").select("*").eq("email", state["email_expediteur"]).execute()
            if res.data:
                contact_data = res.data[0]
                contact_connu = True
                hist = supabase.table("crm_interactions").select("*").eq(
                    "contact_email", state["email_expediteur"]
                ).order("created_at", desc=True).limit(5).execute()
                historique = hist.data if hist.data else []
        except Exception:
            if state.get("mode_demo"):
                contact_data = {
                    "email": state["email_expediteur"],
                    "nom": "Sophie Martin",
                    "entreprise": "TechCorp SAS",
                    "segment": "PME",
                    "valeur_client": 24000,
                    "nb_interactions": 7,
                }
                contact_connu = True
                historique = [
                    {"type": "email", "contenu": "Problème de connexion résolu en J+1", "created_at": "2026-05-15"},
                    {"type": "ticket", "contenu": "Demande de formation clôturée", "created_at": "2026-04-20"},
                ]

        audit_log = log(audit_log, "CRM terminé", "Agent CRM",
            f"Contact {'connu' if contact_connu else 'inconnu'} | {len(historique)} interactions")

        return {
            **state,
            "contact_connu": contact_connu,
            "contact_data": contact_data,
            "historique_interactions": historique,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur CRM : {str(e)}"}


def agent_classification(state: WorkflowState) -> WorkflowState:
    try:
        audit_log = log(state.get("audit_log", []), "Classification email", "Agent Classification")

        prompt = f"""Analyse cet email et reponds avec un JSON valide uniquement, sans backticks, sans texte avant ou apres.

EMAIL :
De : {state['email_expediteur']}
Sujet : {state['email_sujet']}
Corps : {state['email_corps'][:600]}

Reponds avec exactement ce format JSON :
{{
  "categorie": "une des valeurs : Support client — Problème technique | Support client — Facturation | Demande commerciale — Nouveau prospect | Demande commerciale — Upsell | Réclamation formelle | Partenariat | RH / Candidature | Spam / Non pertinent",
  "priorite": "une des valeurs : critique | haute | normale | basse",
  "sentiment": "une des valeurs : positif | neutre | negatif",
  "resume": "resume en 1 phrase courte",
  "entites": {{
    "montant": null,
    "produit": null,
    "action_demandee": null
  }}
}}"""

        reponse = invoke_with_retry(
            system="Tu es un classificateur d emails. Tu reponds UNIQUEMENT avec du JSON valide, rien d autre.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )

        # Nettoyage
        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        data = json.loads(reponse_clean)

        categorie = data.get("categorie", "Autre")
        priorite = data.get("priorite", "normale")
        equipe = EQUIPES.get(categorie, "equipe_direction")
        sla = PRIORITES.get(priorite, {}).get("sla_heures", 24)

        audit_log = log(audit_log, "Classification terminée", "Agent Classification",
            f"Catégorie : {categorie} | Priorité : {priorite} | Équipe : {equipe}")

        return {
            **state,
            "categorie": categorie,
            "priorite": priorite,
            "sentiment": data.get("sentiment", "neutre"),
            "resume": data.get("resume", ""),
            "entites_extraites": data.get("entites", {}),
            "equipe_assignee": equipe or "equipe_direction",
            "sla_heures": sla,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "categorie": "Autre", "priorite": "normale", "sentiment": "neutre",
                "resume": "", "entites_extraites": {}, "equipe_assignee": "equipe_direction",
                "sla_heures": 24, "erreur": f"Erreur classification : {str(e)}"}


def agent_crm_update(state: WorkflowState) -> WorkflowState:
    try:
        audit_log = log(state.get("audit_log", []), "Mise à jour CRM", "Agent CRM Update")

        import random
        ticket_ref = f"TKT-{time.strftime('%Y%m')}-{random.randint(1000, 9999)}"
        relance = time.strftime("%Y-%m-%dT%H:%M:%S",
            time.localtime(time.time() + state["sla_heures"] * 3600))

        actions = state.get("actions_executees", [])

        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

            if not state["contact_connu"]:
                supabase.table("crm_contacts").upsert({
                    "email": state["email_expediteur"],
                    "nom": state["contact_data"].get("nom", ""),
                    "entreprise": state["contact_data"].get("entreprise", ""),
                    "nb_interactions": 1,
                }).execute()
            else:
                supabase.table("crm_contacts").update({
                    "nb_interactions": state["contact_data"].get("nb_interactions", 0) + 1,
                    "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                }).eq("email", state["email_expediteur"]).execute()

            supabase.table("crm_tickets").insert({
                "reference": ticket_ref,
                "contact_email": state["email_expediteur"],
                "sujet": state["email_sujet"],
                "categorie": state["categorie"],
                "priorite": state["priorite"],
                "equipe_assignee": state["equipe_assignee"],
                "sla_heures": state["sla_heures"],
                "relance_programmee": relance,
            }).execute()

            supabase.table("crm_interactions").insert({
                "ticket_reference": ticket_ref,
                "contact_email": state["email_expediteur"],
                "type": "email_entrant",
                "contenu": state["resume"],
                "agent": "workflow_agent",
            }).execute()

            actions.append(f"Ticket {ticket_ref} créé dans Supabase CRM")
            actions.append("Contact mis à jour")
            actions.append("Interaction loggée")

        except Exception:
            actions.append(f"[DEMO] Ticket {ticket_ref} créé")
            actions.append("[DEMO] Contact mis à jour")
            actions.append("[DEMO] Interaction loggée")

        audit_log = log(audit_log, "CRM mis à jour", "Agent CRM Update",
            f"Ticket : {ticket_ref} | Relance : {relance}")

        return {
            **state,
            "ticket_reference": ticket_ref,
            "relance_programmee": relance,
            "actions_executees": actions,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur CRM update : {str(e)}"}


def agent_reponse(state: WorkflowState) -> WorkflowState:
    try:
        audit_log = log(state.get("audit_log", []), "Génération réponse", "Agent Réponse")

        if state["categorie"] == "Spam / Non pertinent":
            return {**state, "reponse_generee": "",
                    "audit_log": log(audit_log, "Spam ignoré", "Agent Réponse"), "erreur": ""}

        contact_nom = state["contact_data"].get("nom", "")
        prenom = contact_nom.split()[0] if contact_nom else "vous"

        prompt = f"""Redige une reponse email professionnelle en francais (150 mots max) :

Contact : {prenom} ({state['contact_data'].get('entreprise', '')})
Categorie : {state['categorie']}
Priorite : {state['priorite']}
Sentiment : {state['sentiment']}
Resume : {state['resume']}
Ticket : {state['ticket_reference']}
Equipe : {state['equipe_assignee']}
SLA : {state['sla_heures']}h

Email original :
Sujet : {state['email_sujet']}
{state['email_corps'][:400]}

Structure : salutation + accuse reception + numero ticket + action concrete + delai + signature."""

        reponse = invoke_with_retry(
            system="Tu es un expert en relation client B2B. Tu rediges des reponses email professionnelles en francais. Tu termines toujours avant de t arreter.",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            model=MODEL_SONNET,
        )

        actions = state.get("actions_executees", [])
        actions.append("Réponse email générée")
        audit_log = log(audit_log, "Réponse générée", "Agent Réponse", f"{len(reponse)} caractères")

        return {**state, "reponse_generee": reponse, "actions_executees": actions, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur réponse : {str(e)}"}


def agent_envoi_gmail(state: WorkflowState) -> WorkflowState:
    try:
        audit_log = log(state.get("audit_log", []), "Envoi Gmail", "Agent Gmail")
        actions = state.get("actions_executees", [])

        if not state["reponse_generee"] or state["mode_demo"]:
            actions.append("[DEMO] Envoi Gmail simulé")
            audit_log = log(audit_log, "Envoi simulé", "Agent Gmail")
            return {**state, "actions_executees": actions, "audit_log": audit_log, "erreur": ""}

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
            with open(GMAIL_TOKEN_FILE, "w") as f:
                f.write(creds.to_json())

        service = build("gmail", "v1", credentials=creds)
        message = MIMEText(state["reponse_generee"], "plain", "utf-8")
        message["to"] = state["email_expediteur"]
        message["subject"] = f"Re: {state['email_sujet']}"
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()

        actions.append(f"Email envoyé à {state['email_expediteur']}")
        audit_log = log(audit_log, "Email envoyé", "Agent Gmail", state["email_expediteur"])
        return {**state, "actions_executees": actions, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur Gmail : {str(e)}"}


def router_spam(state: WorkflowState) -> str:
    if state["categorie"] == "Spam / Non pertinent":
        return "fin"
    return "continuer"


def build_graph():
    graph = StateGraph(WorkflowState)
    graph.add_node("agent_crm_lookup", agent_crm_lookup)
    graph.add_node("agent_classification", agent_classification)
    graph.add_node("agent_crm_update", agent_crm_update)
    graph.add_node("agent_reponse", agent_reponse)
    graph.add_node("agent_envoi_gmail", agent_envoi_gmail)

    graph.set_entry_point("agent_crm_lookup")
    graph.add_edge("agent_crm_lookup", "agent_classification")
    graph.add_conditional_edges(
        "agent_classification",
        router_spam,
        {"continuer": "agent_crm_update", "fin": END}
    )
    graph.add_edge("agent_crm_update", "agent_reponse")
    graph.add_edge("agent_reponse", "agent_envoi_gmail")
    graph.add_edge("agent_envoi_gmail", END)

    return graph.compile()