# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    CLAUSES_OBLIGATOIRES, NIVEAUX_RISQUE
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContratState(TypedDict):
    mode: str
    type_contrat: str
    nom_contrat: str
    contenu_original: str
    parties: dict
    objet: str
    contexte: str
    clauses_extraites: dict
    clauses_manquantes: list
    risques: list
    score_risque: int
    analyse_partie1: str
    analyse_partie2: str
    analyse_complete: str
    contrat_genere: str
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


def agent_extraction_clauses(state: ContratState) -> ContratState:
    """Extrait et structure toutes les clauses du contrat."""
    try:
        audit_log = log(state.get("audit_log", []), "Extraction clauses", "Agent Extraction",
            f"Type : {state['type_contrat']}")

        if state["mode"] == "Générer un nouveau contrat":
            audit_log = log(audit_log, "Mode génération — extraction ignorée", "Agent Extraction")
            return {**state, "clauses_extraites": {}, "clauses_manquantes": [], "audit_log": audit_log, "erreur": ""}

        system = """Tu es un juriste expert en droit des contrats francais.
Tu extrais et structures les clauses contractuelles.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "clauses": {
    "objet": "contenu de la clause ou null",
    "duree": "contenu ou null",
    "prix": "contenu ou null",
    "responsabilite": "contenu ou null",
    "resiliation": "contenu ou null",
    "propriete_intellectuelle": "contenu ou null",
    "confidentialite": "contenu ou null",
    "loi_applicable": "contenu ou null"
  },
  "parties": {
    "partie1": {"nom": "", "forme_juridique": "", "siret": "", "representant": ""},
    "partie2": {"nom": "", "forme_juridique": "", "siret": "", "representant": ""}
  },
  "date_signature": null,
  "duree_contrat": null,
  "montant_total": null
}"""

        prompt = f"""Extrait toutes les clauses de ce contrat :

TYPE : {state['type_contrat']}
NOM : {state['nom_contrat']}

CONTENU :
{state['contenu_original'][:4000]}

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
            data = {"clauses": {}, "parties": {}, "date_signature": None, "duree_contrat": None, "montant_total": None}

        # Détecter les clauses manquantes
        clauses_requises = CLAUSES_OBLIGATOIRES.get(state["type_contrat"], [])
        clauses_presentes = [k for k, v in data.get("clauses", {}).items() if v]
        clauses_manquantes = [c for c in clauses_requises if not any(mot in " ".join(clauses_presentes) for mot in c.lower().split())]

        audit_log = log(audit_log, "Extraction terminée", "Agent Extraction",
            f"{len(clauses_presentes)} clauses | {len(clauses_manquantes)} manquantes")

        return {
            **state,
            "clauses_extraites": data.get("clauses", {}),
            "parties": data.get("parties", {}),
            "clauses_manquantes": clauses_manquantes,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur extraction : {str(e)}"}


def agent_analyse_risques(state: ContratState) -> ContratState:
    """Analyse les risques juridiques et financiers du contrat."""
    try:
        audit_log = log(state.get("audit_log", []), "Analyse risques", "Agent Risques")

        if state["mode"] == "Générer un nouveau contrat":
            audit_log = log(audit_log, "Mode génération — analyse ignorée", "Agent Risques")
            return {**state, "risques": [], "score_risque": 0, "audit_log": audit_log, "erreur": ""}

        system = """Tu es un juriste expert en analyse de risques contractuels.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "risques": [
    {
      "titre": "titre du risque",
      "niveau": "critique|eleve|moyen|faible",
      "clause_concernee": "nom de la clause",
      "description": "description precise",
      "impact": "impact potentiel chiffre si possible",
      "recommandation": "modification a apporter"
    }
  ],
  "score_risque": 65,
  "clauses_abusives": ["clause 1"],
  "illegalites_detectees": ["illegalite 1"]
}"""

        clauses_str = json.dumps(state["clauses_extraites"], ensure_ascii=False, indent=2)

        prompt = f"""Analyse les risques juridiques de ce contrat :

TYPE : {state['type_contrat']}
CLAUSES MANQUANTES : {', '.join(state['clauses_manquantes'][:5])}

CLAUSES EXTRAITES :
{clauses_str[:3000]}

CONTENU ORIGINAL :
{state['contenu_original'][:2000]}

Identifies risques, clauses abusives, illegalites.
Score risque 0-100 (100 = tres risque).
JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=2000)

        reponse_clean = reponse.strip()
        start = reponse_clean.find("{")
        end = reponse_clean.rfind("}") + 1
        if start >= 0 and end > start:
            reponse_clean = reponse_clean[start:end]

        try:
            data = json.loads(reponse_clean)
        except Exception:
            data = {"risques": [], "score_risque": 50, "clauses_abusives": [], "illegalites_detectees": []}

        audit_log = log(audit_log, "Risques analysés", "Agent Risques",
            f"{len(data.get('risques', []))} risques | Score : {data.get('score_risque')}/100")

        return {
            **state,
            "risques": data.get("risques", []),
            "score_risque": data.get("score_risque", 50),
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur risques : {str(e)}"}


def agent_synthese_analyse(state: ContratState) -> ContratState:
    """Génère la synthèse d'analyse avec recommandations."""
    try:
        audit_log = log(state.get("audit_log", []), "Synthèse analyse", "Agent Synthèse")

        if state["mode"] == "Générer un nouveau contrat":
            audit_log = log(audit_log, "Mode génération — synthèse ignorée", "Agent Synthèse")
            return {**state, "analyse_complete": "", "audit_log": audit_log, "erreur": ""}

        system = """Tu es un juriste senior expert en droit des contrats.
Tu rediges des analyses contractuelles professionnelles en francais.
Tu termines TOUJOURS avant de t arreter."""

        risques_str = "\n".join([
            f"[{NIVEAUX_RISQUE.get(r.get('niveau','moyen'))} {r.get('niveau','').upper()}] {r.get('titre','')} : {r.get('description','')[:100]}"
            for r in state["risques"][:6]
        ])

        prompt = f"""Redige la synthese d analyse contractuelle (max 400 mots) :

CONTRAT : {state['nom_contrat']}
TYPE : {state['type_contrat']}
SCORE RISQUE : {state['score_risque']}/100
CLAUSES MANQUANTES : {', '.join(state['clauses_manquantes'][:5]) or 'Aucune'}

RISQUES :
{risques_str or 'Aucun risque identifie'}

Structure :
1. VERDICT (1 phrase : signer / negocier / refuser)
2. POINTS CLES (4 points max)
3. RISQUES PRIORITAIRES (top 3 avec recommandation)
4. ACTIONS AVANT SIGNATURE (5 actions concretes)
5. VERDICT FINAL (1 phrase avec conditions)

Termine le verdict final."""

        synthese = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Synthèse terminée", "Agent Synthèse", f"{len(synthese)} caractères")

        return {
            **state,
            "analyse_complete": synthese,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur synthèse : {str(e)}"}


def agent_generation_contrat(state: ContratState) -> ContratState:
    """Génère ou améliore le contrat."""
    try:
        audit_log = log(state.get("audit_log", []), "Génération contrat", "Agent Génération")

        if state["mode"] == "Analyser un contrat existant":
            audit_log = log(audit_log, "Mode analyse — génération ignorée", "Agent Génération")
            return {**state, "contrat_genere": "", "audit_log": audit_log, "erreur": ""}

        system = """Tu es un juriste expert en redaction de contrats francais.
Tu rediges des contrats conformes au droit francais avec toutes les mentions obligatoires.
Tu termines TOUJOURS avant de t arreter."""

        if state["mode"] == "Analyser ET générer une version améliorée":
            risques_str = "\n".join([
                f"- {r.get('titre','')} : {r.get('recommandation','')}"
                for r in state["risques"][:5]
            ])
            prompt = f"""Genere une version AMELIOREE de ce contrat en corrigeant tous les risques identifies :

TYPE : {state['type_contrat']}
RISQUES A CORRIGER :
{risques_str}
CLAUSES MANQUANTES A AJOUTER : {', '.join(state['clauses_manquantes'][:5])}

CONTRAT ORIGINAL :
{state['contenu_original'][:3000]}

Genere le contrat complet ameliore avec toutes les corrections.
Termine le contrat avec les signatures."""
        else:
            parties = state.get("parties", {})
            prompt = f"""Genere un contrat complet de type {state['type_contrat']} :

PARTIES :
- Partie 1 : {parties.get('partie1', {}).get('nom', 'Société A')}
- Partie 2 : {parties.get('partie2', {}).get('nom', 'Société B')}

OBJET : {state['objet']}
CONTEXTE : {state['contexte']}

Genere un contrat complet avec :
- En-tete et identification des parties
- Toutes les clauses obligatoires pour ce type de contrat
- Mentions legales requises par le droit francais
- Clause de signature

Termine avec les lignes de signature."""

        contrat = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            model=MODEL_SONNET,
        )

        # Sauvegarder dans Supabase
        try:
            from supabase import create_client
            import os
            supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
            supabase.table("contrats").insert({
                "nom": state["nom_contrat"],
                "type_contrat": state["type_contrat"],
                "score_risque": state["score_risque"],
                "nb_risques_critiques": len([r for r in state["risques"] if r.get("niveau") == "critique"]),
                "contenu_original": state["contenu_original"][:5000] if state["contenu_original"] else "",
                "contenu_ameliore": contrat[:5000],
            }).execute()
        except Exception:
            pass

        audit_log = log(audit_log, "Contrat généré", "Agent Génération", f"{len(contrat)} caractères")

        return {
            **state,
            "contrat_genere": contrat,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur génération : {str(e)}"}


def build_graph():
    graph = StateGraph(ContratState)
    graph.add_node("agent_extraction_clauses", agent_extraction_clauses)
    graph.add_node("agent_analyse_risques", agent_analyse_risques)
    graph.add_node("agent_synthese_analyse", agent_synthese_analyse)
    graph.add_node("agent_generation_contrat", agent_generation_contrat)

    graph.set_entry_point("agent_extraction_clauses")
    graph.add_edge("agent_extraction_clauses", "agent_analyse_risques")
    graph.add_edge("agent_analyse_risques", "agent_synthese_analyse")
    graph.add_edge("agent_synthese_analyse", "agent_generation_contrat")
    graph.add_edge("agent_generation_contrat", END)

    return graph.compile()