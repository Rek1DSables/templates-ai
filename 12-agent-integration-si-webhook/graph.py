# graph.py
import time
import json
import hashlib
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    CODES_ERREUR, STRATEGIES_RETRY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class SIState(TypedDict):
    # Input
    type_integration: str
    payload_entrant: dict
    systeme_source: str
    systemes_destinations: list
    strategie_retry: str
    mode_demo: bool

    # Processing
    event_id: str
    payload_valide: bool
    erreurs_validation: list
    payload_transforme: dict
    mapping_effectue: dict
    tentatives: dict
    resultats_envoi: list
    dead_letter: list

    # Output
    rapport_integration: str
    statut_global: str
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


def agent_reception_validation(state: SIState) -> SIState:
    """Reçoit, valide et déduplique le payload entrant."""
    try:
        audit_log = log(state.get("audit_log", []), "Réception & Validation", "Agent Réception",
            f"Source : {state['systeme_source']} | Type : {state['type_integration']}")

        # Génération event_id idempotent
        payload_str = json.dumps(state["payload_entrant"], sort_keys=True)
        event_id = hashlib.sha256(payload_str.encode()).hexdigest()[:16]

        # Validation IA du payload
        system = """Tu es un expert en integration de systemes d information.
Tu valides les payloads entrants et detectes les anomalies.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "valide": true,
  "erreurs": [],
  "type_detecte": "payment | lead | alert | pr | custom",
  "champs_requis_manquants": [],
  "champs_suspects": [],
  "score_qualite": 95
}"""

        prompt = f"""Valide ce payload entrant :

TYPE INTEGRATION : {state['type_integration']}
SOURCE : {state['systeme_source']}

PAYLOAD :
{json.dumps(state['payload_entrant'], ensure_ascii=False, indent=2)[:2000]}

Verifie : structure, champs requis, types de donnees, valeurs suspectes.
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=400)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        try:
            data = json.loads(reponse_clean)
        except Exception:
            data = {"valide": True, "erreurs": [], "type_detecte": "custom",
                    "champs_requis_manquants": [], "score_qualite": 80}

        # Sauvegarder dans Supabase
        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            supabase.table("si_events").upsert({
                "event_id": event_id,
                "type_integration": state["type_integration"],
                "payload_original": state["payload_entrant"],
                "statut": "recu",
            }).execute()
        except Exception:
            pass

        audit_log = log(audit_log, "Validation terminée", "Agent Réception",
            f"Event ID : {event_id} | Valide : {data.get('valide')} | Score : {data.get('score_qualite')}/100")

        return {
            **state,
            "event_id": event_id,
            "payload_valide": data.get("valide", True),
            "erreurs_validation": data.get("erreurs", []),
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur réception : {str(e)}"}


def agent_transformation_mapping(state: SIState) -> SIState:
    """Transforme et mappe le payload vers le format des destinations."""
    try:
        audit_log = log(state.get("audit_log", []), "Transformation & Mapping", "Agent Transformation")

        system = """Tu es un expert en transformation de donnees et integration SI.
Tu transformes les payloads entre differents formats et systemes.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "payload_transforme": {},
  "mappings": [
    {"source": "champ_source", "destination": "champ_destination", "transformation": "description"}
  ],
  "enrichissements": ["enrichissement 1"],
  "payload_par_destination": {
    "CRM": {},
    "Slack": {},
    "Base de données": {}
  }
}"""

        destinations_str = ", ".join(state["systemes_destinations"])

        prompt = f"""Transforme ce payload pour les destinations suivantes :

EVENT ID : {state['event_id']}
TYPE : {state['type_integration']}
DESTINATIONS : {destinations_str}

PAYLOAD ORIGINAL :
{json.dumps(state['payload_entrant'], ensure_ascii=False, indent=2)[:2000]}

Pour chaque destination, adapte le format selon ses conventions.
Enrichis avec des champs calcules si pertinent (timestamps, IDs derives, etc.).
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=1500)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        try:
            data = json.loads(reponse_clean)
        except Exception:
            data = {
                "payload_transforme": state["payload_entrant"],
                "mappings": [],
                "enrichissements": [],
                "payload_par_destination": {d: state["payload_entrant"] for d in state["systemes_destinations"]},
            }

        audit_log = log(audit_log, "Transformation terminée", "Agent Transformation",
            f"{len(data.get('mappings', []))} mappings | {len(data.get('enrichissements', []))} enrichissements")

        return {
            **state,
            "payload_transforme": data.get("payload_transforme", {}),
            "mapping_effectue": {
                "mappings": data.get("mappings", []),
                "enrichissements": data.get("enrichissements", []),
                "payload_par_destination": data.get("payload_par_destination", {}),
            },
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur transformation : {str(e)}"}


def agent_envoi_retry(state: SIState) -> SIState:
    """Envoie le payload transformé vers les destinations avec retry et dead letter."""
    try:
        audit_log = log(state.get("audit_log", []), "Envoi & Retry", "Agent Envoi",
            f"{len(state['systemes_destinations'])} destinations")

        strategie = STRATEGIES_RETRY.get(state["strategie_retry"], STRATEGIES_RETRY["exponential"])
        resultats = []
        dead_letter = []
        tentatives_log = {}

        payload_par_dest = state["mapping_effectue"].get("payload_par_destination", {})

        for destination in state["systemes_destinations"]:
            payload_dest = payload_par_dest.get(destination, state["payload_transforme"])
            tentatives = 0
            succes = False
            dernier_statut = 0
            dernier_message = ""

            while tentatives < strategie["max_attempts"] and not succes:
                tentatives += 1

                if state["mode_demo"]:
                    # Simulation d'envoi en mode démo
                    import random
                    # Simuler quelques erreurs pour démonstration
                    if tentatives == 1 and "ERP" in destination:
                        code_simule = 503
                    elif tentatives <= 2 and "ERP" in destination:
                        code_simule = 503
                    else:
                        code_simule = 200

                    dernier_statut = code_simule
                    comportement = CODES_ERREUR.get(code_simule, ("unknown", "retry"))[1]

                    if code_simule in [200, 201]:
                        succes = True
                        dernier_message = f"[DEMO] Envoi simulé vers {destination} — HTTP {code_simule}"
                    elif comportement == "dead_letter":
                        dernier_message = f"[DEMO] Erreur permanente {code_simule} → Dead Letter"
                        break
                    else:
                        delay = strategie["delay_base"] * (2 ** (tentatives - 1)) if state["strategie_retry"] == "exponential" else strategie["delay_base"]
                        dernier_message = f"[DEMO] Tentative {tentatives} — HTTP {code_simule} — Retry dans {delay}s"
                        if not state["mode_demo"]:
                            time.sleep(min(delay, 5))
                else:
                    # Envoi réel (webhook HTTP)
                    try:
                        r = requests.post(
                            destination,
                            json=payload_dest,
                            timeout=10,
                            headers={"Content-Type": "application/json", "X-Event-ID": state["event_id"]},
                        )
                        dernier_statut = r.status_code
                        comportement = CODES_ERREUR.get(r.status_code, ("unknown", "retry"))[1]

                        if r.status_code in [200, 201]:
                            succes = True
                            dernier_message = f"HTTP {r.status_code} — {r.text[:100]}"
                        elif comportement == "dead_letter":
                            dernier_message = f"Erreur permanente HTTP {r.status_code}"
                            break
                        else:
                            delay = strategie["delay_base"] * (2 ** (tentatives - 1))
                            time.sleep(min(delay, 30))
                            dernier_message = f"Tentative {tentatives} — HTTP {r.status_code}"
                    except Exception as e:
                        dernier_message = f"Erreur connexion : {str(e)}"
                        time.sleep(strategie["delay_base"])

            tentatives_log[destination] = tentatives

            resultat = {
                "destination": destination,
                "succes": succes,
                "tentatives": tentatives,
                "code_http": dernier_statut,
                "message": dernier_message,
                "event_id": state["event_id"],
            }
            resultats.append(resultat)

            if not succes:
                dead_letter.append({
                    "event_id": state["event_id"],
                    "destination": destination,
                    "payload": payload_dest,
                    "erreur": dernier_message,
                    "tentatives": tentatives,
                })
                try:
                    from supabase import create_client
                    import os
                    supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
                    supabase.table("si_dead_letter").insert({
                        "event_id": state["event_id"],
                        "erreur": dernier_message,
                        "payload": payload_dest,
                    }).execute()
                except Exception:
                    pass

            audit_log = log(audit_log, f"Envoi {destination}", "Agent Envoi",
                f"{'✅' if succes else '❌'} | {tentatives} tentative(s) | HTTP {dernier_statut}")

        # Mettre à jour statut dans Supabase
        statut_global = "success" if all(r["succes"] for r in resultats) else "partial" if any(r["succes"] for r in resultats) else "failed"
        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            supabase.table("si_events").update({
                "statut": statut_global,
                "tentatives": max(tentatives_log.values()) if tentatives_log else 1,
                "payload_transforme": state["payload_transforme"],
                "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            }).eq("event_id", state["event_id"]).execute()
        except Exception:
            pass

        audit_log = log(audit_log, "Envoi terminé", "Agent Envoi",
            f"Statut : {statut_global} | {len([r for r in resultats if r['succes']])}/{len(resultats)} succès | {len(dead_letter)} dead letters")

        return {
            **state,
            "resultats_envoi": resultats,
            "dead_letter": dead_letter,
            "tentatives": tentatives_log,
            "statut_global": statut_global,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur envoi : {str(e)}"}


def agent_rapport_integration(state: SIState) -> SIState:
    """Génère le rapport d'intégration avec métriques et recommandations."""
    try:
        audit_log = log(state.get("audit_log", []), "Rapport intégration", "Agent Rapport")

        system = """Tu es un expert en integration SI et architecture evenementielle.
Tu rediges des rapports d integration concis en francais professionnel.
Tu termines TOUJOURS avant de t arreter."""

        resultats_str = "\n".join([
            f"- {'✅' if r['succes'] else '❌'} {r['destination']} : {r['tentatives']} tentative(s) | HTTP {r['code_http']}"
            for r in state["resultats_envoi"]
        ])

        prompt = f"""Redige un rapport d integration SI concis (max 200 mots) :

EVENT ID : {state['event_id']}
TYPE : {state['type_integration']}
STATUT GLOBAL : {state['statut_global'].upper()}
DESTINATIONS : {len(state['resultats_envoi'])}
SUCCES : {len([r for r in state['resultats_envoi'] if r['succes']])}
DEAD LETTERS : {len(state['dead_letter'])}

RESULTATS :
{resultats_str}

Structure :
STATUT : succes total / partiel / echec
METRIQUES : tentatives moyennes, taux de succes
DEAD LETTERS : actions si applicable
RECOMMANDATIONS : 2-3 points d amelioration

Termine les recommandations."""

        rapport = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Pipeline SI terminé", "system",
            f"Event {state['event_id']} | Statut : {state['statut_global']} | {len(state['dead_letter'])} dead letters")

        return {
            **state,
            "rapport_integration": rapport,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur rapport : {str(e)}"}


def router_validation(state: SIState) -> str:
    if not state["payload_valide"] and state["erreurs_validation"]:
        return "dead_letter"
    return "continuer"


def build_graph():
    graph = StateGraph(SIState)
    graph.add_node("agent_reception_validation", agent_reception_validation)
    graph.add_node("agent_transformation_mapping", agent_transformation_mapping)
    graph.add_node("agent_envoi_retry", agent_envoi_retry)
    graph.add_node("agent_rapport_integration", agent_rapport_integration)

    graph.set_entry_point("agent_reception_validation")
    graph.add_conditional_edges(
        "agent_reception_validation",
        router_validation,
        {
            "continuer": "agent_transformation_mapping",
            "dead_letter": "agent_rapport_integration",
        }
    )
    graph.add_edge("agent_transformation_mapping", "agent_envoi_retry")
    graph.add_edge("agent_envoi_retry", "agent_rapport_integration")
    graph.add_edge("agent_rapport_integration", END)

    return graph.compile()