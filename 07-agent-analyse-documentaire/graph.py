# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    AXES_PAR_TYPE, AXES_DEFAUT, NIVEAUX_RISQUE
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class DocumentAnalyseState(TypedDict):
    type_document: str
    contenu_document: str
    nom_document: str
    axes_analyse: list
    extractions: dict
    risques: list
    score_risque: int
    matrice_conformite: list
    synthese_partie1: str
    synthese_partie2: str
    synthese_complete: str
    recommandations: list
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


def agent_extraction(state: DocumentAnalyseState) -> DocumentAnalyseState:
    """Extrait les données structurées pour chaque axe d'analyse."""
    try:
        audit_log = log(state.get("audit_log", []), "Extraction structurée", "Agent Extraction",
            f"{len(state['axes_analyse'])} axes | {len(state['contenu_document'])} caractères")

        extractions = {}
        contenu = state["contenu_document"][:5000]

        system = """Tu es un expert juridique et financier specialise en analyse documentaire.
Tu extrais des informations precises depuis des documents complexes.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "valeur": "information extraite precise ou null si absent",
  "present": true,
  "localisation": "section ou page approximative",
  "fiabilite": "haute|moyenne|faible",
  "alerte": null
}"""

        for axe in state["axes_analyse"]:
            prompt = f"""Extrait l information suivante du document :

AXE : {axe}
TYPE DOCUMENT : {state['type_document']}

DOCUMENT :
{contenu}

Extrait la valeur precise pour cet axe. Si absent, indique null.
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
                data = {"valeur": None, "present": False, "localisation": "", "fiabilite": "faible", "alerte": None}

            extractions[axe] = data
            audit_log = log(audit_log, f"Axe extrait", "Agent Extraction",
                f"{axe[:40]} — {'✅' if data.get('present') else '❌'}")

        return {
            **state,
            "extractions": extractions,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur extraction : {str(e)}"}


def agent_verification_risques(state: DocumentAnalyseState) -> DocumentAnalyseState:
    """Identifie les risques et vérifie la cohérence des extractions."""
    try:
        audit_log = log(state.get("audit_log", []), "Vérification risques", "Agent Vérification")

        system = """Tu es un expert en analyse de risques juridiques et financiers.
Tu identifies les risques dans les documents et verifie la coherence des extractions.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "risques": [
    {
      "titre": "titre du risque",
      "niveau": "critique|eleve|moyen|faible",
      "axe_concerne": "axe d analyse",
      "description": "description precise",
      "impact": "impact potentiel",
      "mitigation": "comment mitiger"
    }
  ],
  "score_risque": 65,
  "incoherences": ["incoherence 1"],
  "elements_manquants": ["element manquant critique 1"]
}"""

        extractions_str = json.dumps(state["extractions"], ensure_ascii=False, indent=2)

        prompt = f"""Analyse les risques de ce document :

TYPE : {state['type_document']}
NOM : {state['nom_document']}

EXTRACTIONS EFFECTUEES :
{extractions_str[:3000]}

DOCUMENT (extrait) :
{state['contenu_document'][:2000]}

Identifies tous les risques, incoherences et elements manquants critiques.
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
            data = {"risques": [], "score_risque": 50, "incoherences": [], "elements_manquants": []}

        # Matrice de conformité
        matrice = []
        for axe, extraction in state["extractions"].items():
            matrice.append({
                "axe": axe,
                "present": extraction.get("present", False),
                "fiabilite": extraction.get("fiabilite", "faible"),
                "alerte": extraction.get("alerte"),
            })

        audit_log = log(audit_log, "Risques identifiés", "Agent Vérification",
            f"{len(data.get('risques', []))} risques | Score : {data.get('score_risque')}/100")

        return {
            **state,
            "risques": data.get("risques", []),
            "score_risque": data.get("score_risque", 50),
            "matrice_conformite": matrice,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur vérification : {str(e)}"}


def agent_synthese_partie1(state: DocumentAnalyseState) -> DocumentAnalyseState:
    """Génère la première partie de la synthèse : executive summary + extraction détaillée."""
    try:
        audit_log = log(state.get("audit_log", []), "Synthèse partie 1", "Agent Synthèse")

        system = """Tu es un expert juridique et financier senior.
Tu rediges des syntheses d analyse documentaire en francais professionnel.
Tu termines TOUJOURS ta section avant de t arreter."""

        risques_str = "\n".join([
            f"[{r.get('niveau', '').upper()}] {r.get('titre', '')} : {r.get('description', '')}"
            for r in state["risques"][:5]
        ])

        extractions_resume = "\n".join([
            f"- {axe} : {data.get('valeur', 'Non trouvé') or 'Non trouvé'}"
            for axe, data in list(state["extractions"].items())[:6]
        ])

        prompt = f"""Redige la PARTIE 1 de l analyse documentaire :

DOCUMENT : {state['nom_document']}
TYPE : {state['type_document']}
SCORE RISQUE : {state['score_risque']}/100

EXTRACTIONS CLES :
{extractions_resume}

RISQUES IDENTIFIES :
{risques_str if risques_str else 'Aucun risque critique identifié'}

Redige ces 2 sections (max 300 mots total) :

1. SYNTHESE EXECUTIVE
- Verdict en 1 phrase (document favorable / a negocier / risque eleve)
- 4 points cles du document
- Score de risque global justifie

2. INFORMATIONS EXTRAITES
- Resume structure de chaque axe analyse
- Signaler les elements absents ou incomplets

Termine imperativement la section 2."""

        synthese = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            model=MODEL_SONNET,
        )

        audit_log = log(audit_log, "Synthèse partie 1 terminée", "Agent Synthèse")

        return {
            **state,
            "synthese_partie1": synthese,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur synthèse partie 1 : {str(e)}"}


def agent_synthese_partie2(state: DocumentAnalyseState) -> DocumentAnalyseState:
    """Génère la deuxième partie : matrice risques + recommandations + verdict."""
    try:
        audit_log = log(state.get("audit_log", []), "Synthèse partie 2", "Agent Synthèse")

        system = """Tu es un expert juridique et financier senior.
Tu rediges des syntheses d analyse documentaire en francais professionnel.
Tu termines TOUJOURS ta section avant de t arreter."""

        risques_str = "\n".join([
            f"[{NIVEAUX_RISQUE.get(r.get('niveau', 'moyen'), '🟡')} {r.get('niveau', '').upper()}] {r.get('titre', '')}\n"
            f"  Impact : {r.get('impact', '')} | Mitigation : {r.get('mitigation', '')}"
            for r in state["risques"]
        ])

        prompt = f"""Redige la PARTIE 2 de l analyse documentaire :

DOCUMENT : {state['nom_document']}
TYPE : {state['type_document']}
SCORE RISQUE : {state['score_risque']}/100

RISQUES :
{risques_str if risques_str else 'Aucun risque identifie'}

Redige ces 2 sections (max 300 mots total) :

3. MATRICE DES RISQUES
- Liste chaque risque par niveau (critique → faible)
- Impact et plan de mitigation pour chaque risque

4. RECOMMANDATIONS ET VERDICT FINAL
- 5 actions concretes prioritaires avec responsable et delai
- Verdict final : signer tel quel / negocier avant signature / ne pas signer
- 3 conditions minimales si negotiation requise

Termine imperativement le verdict final."""

        synthese = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            model=MODEL_SONNET,
        )

        synthese_complete = state["synthese_partie1"] + "\n\n" + synthese

        audit_log = log(audit_log, "Analyse documentaire terminée", "system",
            f"Score risque : {state['score_risque']}/100 | {len(state['risques'])} risques | {len(state['extractions'])} axes")

        return {
            **state,
            "synthese_partie2": synthese,
            "synthese_complete": synthese_complete,
            "audit_log": audit_log,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur synthèse partie 2 : {str(e)}"}


def build_graph():
    graph = StateGraph(DocumentAnalyseState)
    graph.add_node("agent_extraction", agent_extraction)
    graph.add_node("agent_verification_risques", agent_verification_risques)
    graph.add_node("agent_synthese_partie1", agent_synthese_partie1)
    graph.add_node("agent_synthese_partie2", agent_synthese_partie2)

    graph.set_entry_point("agent_extraction")
    graph.add_edge("agent_extraction", "agent_verification_risques")
    graph.add_edge("agent_verification_risques", "agent_synthese_partie1")
    graph.add_edge("agent_synthese_partie1", "agent_synthese_partie2")
    graph.add_edge("agent_synthese_partie2", END)

    return graph.compile()