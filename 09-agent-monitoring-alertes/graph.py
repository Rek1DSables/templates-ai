# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    NIVEAUX_ALERTE, SEUILS_DEFAUT
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class MonitoringState(TypedDict):
    # Input
    metriques: dict
    seuils: dict
    type_metriques: str
    contexte_business: str
    destinataire_email: str
    envoyer_email: bool
    mode_demo: bool

    # Processing
    violations: list
    alertes_generees: list
    analyse_causale: str
    actions_recommandees: list
    score_sante: int
    tendances: list

    # Output
    rapport_monitoring: str
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


def agent_detection_violations(state: MonitoringState) -> MonitoringState:
    """Détecte les violations de seuils sur les métriques."""
    try:
        audit_log = log(state.get("audit_log", []), "Détection violations", "Agent Détection",
            f"{len(state['metriques'])} métriques analysées")

        violations = []
        seuils = state.get("seuils", SEUILS_DEFAUT)

        for metrique, valeur in state["metriques"].items():
            if metrique not in seuils:
                continue

            seuil_config = seuils[metrique]
            seuil = seuil_config.get("seuil", 0)
            direction = seuil_config.get("direction", "above")
            unite = seuil_config.get("unite", "")

            violation = False
            ecart_pct = 0

            if direction == "above" and float(valeur) > float(seuil):
                violation = True
                ecart_pct = ((float(valeur) - float(seuil)) / float(seuil)) * 100 if seuil != 0 else 100
            elif direction == "below" and float(valeur) < float(seuil):
                violation = True
                ecart_pct = ((float(seuil) - float(valeur)) / float(seuil)) * 100 if seuil != 0 else 100

            if violation:
                # Déterminer le niveau selon l'écart
                if ecart_pct > 50:
                    niveau = "critique"
                elif ecart_pct > 25:
                    niveau = "eleve"
                elif ecart_pct > 10:
                    niveau = "moyen"
                else:
                    niveau = "info"

                violations.append({
                    "metrique": metrique,
                    "valeur_actuelle": float(valeur),
                    "seuil": float(seuil),
                    "unite": unite,
                    "direction": direction,
                    "ecart_pct": round(ecart_pct, 1),
                    "niveau": niveau,
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                })

        audit_log = log(audit_log, "Violations détectées", "Agent Détection",
            f"{len(violations)} violations | Critiques : {len([v for v in violations if v['niveau'] == 'critique'])}")

        return {
            **state,
            "violations": violations,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur détection : {str(e)}"}


def agent_analyse_causale(state: MonitoringState) -> MonitoringState:
    """Analyse les causes probables et corrélations entre les violations."""
    try:
        audit_log = log(state.get("audit_log", []), "Analyse causale", "Agent Analyse")

        if not state["violations"]:
            audit_log = log(audit_log, "Aucune violation", "Agent Analyse", "Système sain")
            return {
                **state,
                "analyse_causale": "Aucune violation détectée — système dans les seuils normaux.",
                "tendances": [],
                "score_sante": 100,
                "audit_log": audit_log,
                "erreur": "",
            }

        system = """Tu es un expert en monitoring et observabilite systemes.
Tu analyses les violations de metriques et identifies les causes probables.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "analyse": "analyse causale en 2-3 paragraphes",
  "correlations": ["correlation 1", "correlation 2"],
  "cause_racine_probable": "cause racine principale",
  "tendances": ["tendance 1", "tendance 2"],
  "score_sante": 45,
  "urgence": "immediate|court_terme|surveillance"
}"""

        violations_str = json.dumps(state["violations"], ensure_ascii=False, indent=2)
        metriques_str = json.dumps(state["metriques"], ensure_ascii=False)

        prompt = f"""Analyse ces violations de metriques :

TYPE : {state['type_metriques']}
CONTEXTE : {state['contexte_business']}

METRIQUES ACTUELLES :
{metriques_str}

VIOLATIONS DETECTEES :
{violations_str}

Identifies les causes probables, correlations et tendances.
Score de sante global 0-100 (100 = parfait).
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=1000)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        try:
            data = json.loads(reponse_clean)
        except Exception:
            data = {"analyse": "Analyse indisponible", "correlations": [], "cause_racine_probable": "",
                    "tendances": [], "score_sante": 50, "urgence": "surveillance"}

        audit_log = log(audit_log, "Analyse terminée", "Agent Analyse",
            f"Score santé : {data.get('score_sante')}/100 | Urgence : {data.get('urgence')}")

        return {
            **state,
            "analyse_causale": data.get("analyse", ""),
            "tendances": data.get("tendances", []),
            "score_sante": data.get("score_sante", 50),
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def agent_generation_alertes(state: MonitoringState) -> MonitoringState:
    """Génère les alertes structurées et les sauvegarde."""
    try:
        audit_log = log(state.get("audit_log", []), "Génération alertes", "Agent Alertes")

        alertes = []
        actions = []

        system = """Tu es un expert en operations et incident management.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "message_alerte": "message d alerte clair et actionnable",
  "cause_probable": "cause probable en 1 phrase",
  "action_immediate": "action a prendre maintenant",
  "responsable": "qui doit agir",
  "delai": "sous combien de temps"
}"""

        for violation in state["violations"]:
            prompt = f"""Genere une alerte pour cette violation :

METRIQUE : {violation['metrique']}
VALEUR : {violation['valeur_actuelle']} {violation['unite']}
SEUIL : {violation['seuil']} {violation['unite']}
ECART : {violation['ecart_pct']}%
NIVEAU : {violation['niveau']}
CONTEXTE : {state['contexte_business']}

Message d alerte clair, cause probable, action immediate.
JSON uniquement."""

            reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=300)

            reponse_clean = reponse.strip()
            start = reponse_clean.find("{")
            end = reponse_clean.rfind("}") + 1
            if start >= 0 and end > start:
                reponse_clean = reponse_clean[start:end]

            try:
                data = json.loads(reponse_clean)
            except Exception:
                data = {"message_alerte": f"Violation seuil : {violation['metrique']}",
                        "cause_probable": "Analyse manuelle requise",
                        "action_immediate": "Vérifier immédiatement",
                        "responsable": "Équipe ops", "delai": "Immédiat"}

            alerte = {
                **violation,
                "message": data.get("message_alerte", ""),
                "cause_probable": data.get("cause_probable", ""),
                "action_immediate": data.get("action_immediate", ""),
                "responsable": data.get("responsable", ""),
                "delai": data.get("delai", ""),
                "sla_minutes": NIVEAUX_ALERTE.get(violation["niveau"], {}).get("sla_minutes", 60),
                "statut": "ouverte",
            }
            alertes.append(alerte)
            actions.append(f"[{violation['niveau'].upper()}] {data.get('action_immediate', '')} — {data.get('responsable', '')} — {data.get('delai', '')}")

        # Sauvegarder dans Supabase
        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            for alerte in alertes:
                supabase.table("monitoring_alertes").insert({
                    "niveau": alerte["niveau"],
                    "metrique": alerte["metrique"],
                    "valeur_actuelle": alerte["valeur_actuelle"],
                    "seuil": alerte["seuil"],
                    "message": alerte["message"],
                    "cause_probable": alerte["cause_probable"],
                    "action_recommandee": alerte["action_immediate"],
                }).execute()
        except Exception:
            pass

        audit_log = log(audit_log, "Alertes générées", "Agent Alertes",
            f"{len(alertes)} alertes | {len([a for a in alertes if a['niveau'] == 'critique'])} critiques")

        return {
            **state,
            "alertes_generees": alertes,
            "actions_recommandees": actions,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur alertes : {str(e)}"}


def agent_rapport_notification(state: MonitoringState) -> MonitoringState:
    """Génère le rapport de monitoring et envoie les notifications."""
    try:
        audit_log = log(state.get("audit_log", []), "Rapport et notification", "Agent Rapport")

        system = """Tu es un expert en operations et reporting.
Tu rediges des rapports de monitoring concis en francais professionnel.
Tu termines TOUJOURS avant de t arreter."""

        violations_resume = "\n".join([
            f"- [{v['niveau'].upper()}] {v['metrique']} : {v['valeur_actuelle']} (seuil {v['seuil']}) — écart {v['ecart_pct']}%"
            for v in state["violations"]
        ]) if state["violations"] else "Aucune violation"

        actions_str = "\n".join(state["actions_recommandees"][:5]) if state["actions_recommandees"] else "Aucune action requise"

        prompt = f"""Redige un rapport de monitoring concis (150 mots max) :

TYPE : {state['type_metriques']}
SCORE SANTE : {state['score_sante']}/100
VIOLATIONS : {len(state['violations'])}
ALERTES CRITIQUES : {len([a for a in state['alertes_generees'] if a['niveau'] == 'critique'])}

RESUME VIOLATIONS :
{violations_resume}

ACTIONS RECOMMANDEES :
{actions_str}

ANALYSE CAUSALE :
{state['analyse_causale'][:300]}

Format : statut global + violations cles + actions prioritaires.
Termine les actions prioritaires."""

        rapport = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            model=MODEL_SONNET,
        )

        # Envoi email si activé
        if state["envoyer_email"] and state["destinataire_email"] and not state["mode_demo"]:
            try:
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
                nb_critiques = len([a for a in state["alertes_generees"] if a["niveau"] == "critique"])
                sujet = f"🚨 ALERTE MONITORING — {nb_critiques} critique(s) — Score santé {state['score_sante']}/100"

                corps = f"""RAPPORT DE MONITORING — {time.strftime('%d/%m/%Y %H:%M')}

Score de santé : {state['score_sante']}/100
Violations détectées : {len(state['violations'])}
Alertes critiques : {nb_critiques}

{rapport}

ACTIONS PRIORITAIRES :
{actions_str}

---
Rapport généré automatiquement par Agent Monitoring
"""
                message = MIMEText(corps, "plain", "utf-8")
                message["to"] = state["destinataire_email"]
                message["subject"] = sujet
                raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
                service.users().messages().send(userId="me", body={"raw": raw}).execute()
                audit_log = log(audit_log, "Email envoyé", "Agent Rapport", state["destinataire_email"])
            except Exception as e:
                audit_log = log(audit_log, "Erreur envoi email", "Agent Rapport", str(e))

        audit_log = log(audit_log, "Pipeline monitoring terminé", "system",
            f"Score santé : {state['score_sante']}/100 | {len(state['alertes_generees'])} alertes")

        return {
            **state,
            "rapport_monitoring": rapport,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur rapport : {str(e)}"}


def build_graph():
    graph = StateGraph(MonitoringState)
    graph.add_node("agent_detection_violations", agent_detection_violations)
    graph.add_node("agent_analyse_causale", agent_analyse_causale)
    graph.add_node("agent_generation_alertes", agent_generation_alertes)
    graph.add_node("agent_rapport_notification", agent_rapport_notification)

    graph.set_entry_point("agent_detection_violations")
    graph.add_edge("agent_detection_violations", "agent_analyse_causale")
    graph.add_edge("agent_analyse_causale", "agent_generation_alertes")
    graph.add_edge("agent_generation_alertes", "agent_rapport_notification")
    graph.add_edge("agent_rapport_notification", END)

    return graph.compile()