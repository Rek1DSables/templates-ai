# graph.py
import time
import json
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    SERPER_API_KEY, SERPER_URL,
    SCORE_SEUILS
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class SDRState(TypedDict):
    # Prospect input
    prospects: list
    icp_secteurs: list
    icp_postes: list
    icp_tailles: list
    objectif_sequence: str
    produit_contexte: str
    expediteur_nom: str
    expediteur_poste: str
    envoyer_emails: bool

    # Processing
    prospects_enrichis: list
    prospects_qualifies: list
    sequences_generees: list
    stats: dict
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


def agent_enrichissement(state: SDRState) -> SDRState:
    """Enrichit chaque prospect avec des signaux business via Serper."""
    try:
        audit_log = log(state.get("audit_log", []), "Enrichissement prospects", "Agent Enrichissement",
            f"{len(state['prospects'])} prospects à traiter")

        prospects_enrichis = []

        for prospect in state["prospects"]:
            signaux = []

            # Recherche web si Serper disponible
            if SERPER_API_KEY:
                try:
                    queries = [
                        f"{prospect.get('entreprise', '')} actualité 2026",
                        f"{prospect.get('entreprise', '')} levée de fonds recrutement",
                    ]
                    for query in queries:
                        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
                        res = requests.post(SERPER_URL, headers=headers,
                            json={"q": query, "num": 3}, timeout=8)
                        data = res.json()
                        for item in data.get("organic", [])[:2]:
                            signaux.append(item.get("snippet", "")[:150])
                        time.sleep(0.5)
                except Exception:
                    pass

            # Enrichissement IA
            system = """Tu es un agent SDR expert en qualification de prospects B2B.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "score_icp": 72,
  "segment": "hot",
  "signaux_detectes": ["Signal 1", "Signal 2"],
  "resume_enrichi": "Resume du prospect en 2-3 lignes avec contexte business",
  "angle_approche": "Angle de prospection recommande",
  "objection_probable": "Objection la plus probable"
}"""

            signaux_str = "\n".join(signaux[:4]) if signaux else "Aucun signal détecté"

            prompt = f"""Qualifie ce prospect B2B :

PROSPECT :
- Nom : {prospect.get('prenom', '')} {prospect.get('nom', '')}
- Poste : {prospect.get('poste', '')}
- Entreprise : {prospect.get('entreprise', '')}
- Secteur : {prospect.get('secteur', '')}
- Taille : {prospect.get('taille_entreprise', '')}
- Site : {prospect.get('site_web', '')}

ICP CIBLE :
- Secteurs : {', '.join(state['icp_secteurs'])}
- Postes : {', '.join(state['icp_postes'])}
- Tailles : {', '.join(state['icp_tailles'])}

PRODUIT : {state['produit_contexte']}

SIGNAUX BUSINESS DETECTES :
{signaux_str}

Score ICP sur 100, segment (hot/warm/cold), signaux, resume, angle d approche.
JSON uniquement."""

            reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=600)

            reponse_clean = reponse.strip()
            start = reponse_clean.find("{")
            end = reponse_clean.rfind("}") + 1
            if start >= 0 and end > start:
                reponse_clean = reponse_clean[start:end]

            try:
                data = json.loads(reponse_clean)
            except Exception:
                data = {"score_icp": 50, "segment": "warm", "signaux_detectes": [],
                        "resume_enrichi": "", "angle_approche": "", "objection_probable": ""}

            prospect_enrichi = {
                **prospect,
                "score_icp": data.get("score_icp", 50),
                "segment": data.get("segment", "warm"),
                "signaux_detectes": data.get("signaux_detectes", []),
                "resume_enrichi": data.get("resume_enrichi", ""),
                "angle_approche": data.get("angle_approche", ""),
                "objection_probable": data.get("objection_probable", ""),
                "signaux_bruts": signaux,
            }
            prospects_enrichis.append(prospect_enrichi)

        audit_log = log(audit_log, "Enrichissement terminé", "Agent Enrichissement",
            f"{len(prospects_enrichis)} prospects enrichis")

        return {**state, "prospects_enrichis": prospects_enrichis, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur enrichissement : {str(e)}"}


def agent_scoring_qualification(state: SDRState) -> SDRState:
    """Score et filtre les prospects selon l'ICP."""
    try:
        audit_log = log(state.get("audit_log", []), "Scoring et qualification", "Agent Scoring")

        # Trier par score ICP
        tries = sorted(state["prospects_enrichis"], key=lambda x: x.get("score_icp", 0), reverse=True)

        hot = [p for p in tries if p.get("score_icp", 0) >= SCORE_SEUILS["hot"]]
        warm = [p for p in tries if SCORE_SEUILS["cold"] <= p.get("score_icp", 0) < SCORE_SEUILS["hot"]]
        cold = [p for p in tries if p.get("score_icp", 0) < SCORE_SEUILS["cold"]]

        # Sauvegarder dans Supabase si disponible
        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            for p in tries:
                supabase.table("sdr_prospects").upsert({
                    "email": p.get("email", ""),
                    "nom": p.get("nom", ""),
                    "prenom": p.get("prenom", ""),
                    "entreprise": p.get("entreprise", ""),
                    "poste": p.get("poste", ""),
                    "secteur": p.get("secteur", ""),
                    "score_icp": p.get("score_icp", 0),
                    "segment": p.get("segment", "cold"),
                    "signaux_business": json.dumps(p.get("signaux_detectes", []), ensure_ascii=False),
                    "resume_enrichi": p.get("resume_enrichi", ""),
                }).execute()
        except Exception:
            pass

        stats = {
            "total": len(tries),
            "hot": len(hot),
            "warm": len(warm),
            "cold": len(cold),
            "score_moyen": int(sum(p.get("score_icp", 0) for p in tries) / len(tries)) if tries else 0,
        }

        audit_log = log(audit_log, "Scoring terminé", "Agent Scoring",
            f"Hot: {len(hot)} | Warm: {len(warm)} | Cold: {len(cold)} | Score moyen: {stats['score_moyen']}/100")

        return {
            **state,
            "prospects_qualifies": tries,
            "stats": stats,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur scoring : {str(e)}"}


def agent_generation_sequence(state: SDRState) -> SDRState:
    """Génère une séquence email personnalisée pour chaque prospect qualifié."""
    try:
        audit_log = log(state.get("audit_log", []), "Génération séquences", "Agent Séquence",
            f"{len(state['prospects_qualifies'])} séquences à générer")

        sequences_generees = []

        # Ne générer que pour hot et warm
        prospects_actifs = [p for p in state["prospects_qualifies"] if p.get("segment") in ["hot", "warm"]]

        for prospect in prospects_actifs:
            system = """Tu es un expert SDR en prospection B2B.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "email_1": {
    "sujet": "sujet court et percutant",
    "corps": "email de prospection personnalise (100-150 mots)"
  },
  "email_2": {
    "sujet": "sujet de relance",
    "corps": "relance courte et differente (80-100 mots)"
  },
  "email_3": {
    "sujet": "derniere tentative",
    "corps": "breakup email court (50-70 mots)"
  }
}"""

            prompt = f"""Genere une sequence de 3 emails de prospection B2B ultra-personnalises :

PROSPECT :
- {prospect.get('prenom', '')} {prospect.get('nom', '')} — {prospect.get('poste', '')} chez {prospect.get('entreprise', '')}
- Secteur : {prospect.get('secteur', '')} | Taille : {prospect.get('taille_entreprise', '')}
- Score ICP : {prospect.get('score_icp', 0)}/100 | Segment : {prospect.get('segment', '')}
- Resume : {prospect.get('resume_enrichi', '')}
- Signaux : {', '.join(prospect.get('signaux_detectes', [])[:3])}
- Angle recommande : {prospect.get('angle_approche', '')}
- Objection probable : {prospect.get('objection_probable', '')}

EXPEDITEUR : {state['expediteur_nom']} — {state['expediteur_poste']}
OBJECTIF : {state['objectif_sequence']}
PRODUIT : {state['produit_contexte']}

Emails courts, personnalises, axes sur la valeur. Pas de pitching agressif.
JSON uniquement."""

            reponse = invoke_with_retry(
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1200,
                model=MODEL_SONNET,
            )

            reponse_clean = reponse.strip()
            start = reponse_clean.find("{")
            end = reponse_clean.rfind("}") + 1
            if start >= 0 and end > start:
                reponse_clean = reponse_clean[start:end]

            try:
                emails = json.loads(reponse_clean)
            except Exception:
                emails = {
                    "email_1": {"sujet": f"Question rapide — {prospect.get('entreprise', '')}", "corps": ""},
                    "email_2": {"sujet": "Relance", "corps": ""},
                    "email_3": {"sujet": "Dernière tentative", "corps": ""},
                }

            sequences_generees.append({
                "prospect": prospect,
                "emails": emails,
                "statut": "genere",
            })

            # Sauvegarder séquence en Supabase
            try:
                from supabase import create_client
                import os
                supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                for i, (key, email) in enumerate(emails.items(), 1):
                    supabase.table("sdr_sequences").insert({
                        "prospect_email": prospect.get("email", ""),
                        "etape": i,
                        "sujet": email.get("sujet", ""),
                        "corps": email.get("corps", ""),
                    }).execute()
            except Exception:
                pass

        audit_log = log(audit_log, "Séquences générées", "Agent Séquence",
            f"{len(sequences_generees)} séquences de 3 emails générées")

        return {**state, "sequences_generees": sequences_generees, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur séquences : {str(e)}"}


def agent_envoi_premier_email(state: SDRState) -> SDRState:
    """Envoie le premier email de la séquence si activé."""
    try:
        audit_log = log(state.get("audit_log", []), "Envoi premier email", "Agent Envoi")

        if not state["envoyer_emails"]:
            audit_log = log(audit_log, "Envoi désactivé", "Agent Envoi", "Mode preview uniquement")
            return {**state, "audit_log": audit_log, "erreur": ""}

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
        envoyes = 0

        for sequence in state["sequences_generees"]:
            prospect = sequence["prospect"]
            email_data = sequence["emails"].get("email_1", {})

            if not prospect.get("email") or not email_data.get("corps"):
                continue

            message = MIMEText(email_data["corps"], "plain", "utf-8")
            message["to"] = prospect["email"]
            message["subject"] = email_data["sujet"]
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

            try:
                service.users().messages().send(userId="me", body={"raw": raw}).execute()
                sequence["statut"] = "envoye"
                envoyes += 1
                time.sleep(2)
            except Exception as e:
                sequence["statut"] = f"erreur : {str(e)}"

        audit_log = log(audit_log, "Envoi terminé", "Agent Envoi", f"{envoyes} emails envoyés")
        return {**state, "sequences_generees": state["sequences_generees"], "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur envoi : {str(e)}"}


def build_graph():
    graph = StateGraph(SDRState)
    graph.add_node("agent_enrichissement", agent_enrichissement)
    graph.add_node("agent_scoring_qualification", agent_scoring_qualification)
    graph.add_node("agent_generation_sequence", agent_generation_sequence)
    graph.add_node("agent_envoi_premier_email", agent_envoi_premier_email)

    graph.set_entry_point("agent_enrichissement")
    graph.add_edge("agent_enrichissement", "agent_scoring_qualification")
    graph.add_edge("agent_scoring_qualification", "agent_generation_sequence")
    graph.add_edge("agent_generation_sequence", "agent_envoi_premier_email")
    graph.add_edge("agent_envoi_premier_email", END)

    return graph.compile()