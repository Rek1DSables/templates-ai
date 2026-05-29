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


class DueDiligenceState(TypedDict):
    type_dd: str
    nom_cible: str
    secteur: str
    contexte: str
    documents: dict
    axes_selectionnes: list
    analyse_par_axe: dict
    risques: list
    score_global: int
    synthese: str
    recommandation: str
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


def analyser_axes(state: DueDiligenceState) -> DueDiligenceState:
    try:
        analyse_par_axe = {}
        risques_globaux = []

        system = """Tu es un expert en due diligence M&A.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "note": 7,
  "points_positifs": ["point 1", "point 2"],
  "points_negatifs": ["point 1", "point 2"],
  "risques": [
    {"niveau": "eleve", "titre": "titre", "description": "description", "impact": "impact", "mitigation": "mitigation"}
  ],
  "questions_cles": ["question 1", "question 2"]
}"""

        for axe in state["axes_selectionnes"]:
            contenu_axe = state["documents"].get(axe, "Aucun document fourni.")

            prompt = f"""Analyse cet axe de due diligence :

OPERATION : {state['type_dd']}
CIBLE : {state['nom_cible']} | SECTEUR : {state['secteur']}
AXE : {axe}

INFORMATIONS :
{contenu_axe[:2000]}

Note /10, points positifs, negatifs, risques, questions cles.
JSON uniquement."""

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

            try:
                data = json.loads(reponse_clean)
            except Exception:
                data = {"note": 5, "points_positifs": [], "points_negatifs": [], "risques": [], "questions_cles": []}

            analyse_par_axe[axe] = data
            risques_globaux.extend([{**r, "axe": axe} for r in data.get("risques", [])])

        score = int(sum(v.get("note", 5) for v in analyse_par_axe.values()) / len(analyse_par_axe)) * 10 if analyse_par_axe else 50

        return {
            **state,
            "analyse_par_axe": analyse_par_axe,
            "risques": risques_globaux,
            "score_global": score,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse axes : {str(e)}"}


def generer_synthese_executive(state: DueDiligenceState) -> DueDiligenceState:
    try:
        system = """Tu es un partner senior M&A. Tu rediges en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        nb_critiques = sum(1 for r in state["risques"] if r.get("niveau") == "critique")
        nb_eleves = sum(1 for r in state["risques"] if r.get("niveau") == "eleve")
        notes = {axe: data.get("note", 5) for axe, data in state["analyse_par_axe"].items()}

        prompt = f"""Redige UNIQUEMENT la SYNTHESE EXECUTIVE du rapport de due diligence :

CIBLE : {state['nom_cible']} | TYPE : {state['type_dd']}
SCORE : {state['score_global']}/100
RISQUES : {nb_critiques} critiques, {nb_eleves} eleves
NOTES PAR AXE : {json.dumps(notes, ensure_ascii=False)}
CONTEXTE : {state['contexte']}

Inclure :
- Verdict en 1 phrase (Go / No-Go / Go conditionnel)
- 5 points cles de la situation
- Score de confiance global avec justification
- Principaux atouts et principales preoccupations

Sois concis et percutant. Termine avant de t'arreter."""

        synthese = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            model=MODEL_SONNET,
        )

        return {**state, "synthese": synthese, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur synthese executive : {str(e)}"}


def generer_analyse_axes(state: DueDiligenceState) -> DueDiligenceState:
    try:
        system = """Tu es un partner senior M&A. Tu rediges en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        axes_str = ""
        for axe, data in state["analyse_par_axe"].items():
            axes_str += f"\n{axe} : note {data.get('note')}/10\n"
            axes_str += f"+ {' | '.join(data.get('points_positifs', [])[:2])}\n"
            axes_str += f"- {' | '.join(data.get('points_negatifs', [])[:2])}\n"

        prompt = f"""Redige UNIQUEMENT la section ANALYSE DETAILLEE PAR AXE :

CIBLE : {state['nom_cible']}
AXES : {axes_str}

Pour chaque axe : synthese 3-4 lignes, points forts, points de vigilance, note justifiee.
Sois precis et professionnel. Termine tous les axes."""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            model=MODEL_SONNET,
        )

        partie2 = state["synthese"] + "\n\n" + analyse
        return {**state, "synthese": partie2, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse axes : {str(e)}"}


def generer_matrice_risques(state: DueDiligenceState) -> DueDiligenceState:
    try:
        system = """Tu es un partner senior M&A. Tu rediges en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        risques_str = ""
        for r in state["risques"][:8]:
            risques_str += f"[{r.get('niveau','').upper()}] {r.get('titre','')} ({r.get('axe','')})\n"
            risques_str += f"Impact : {r.get('impact','')}\n"
            risques_str += f"Mitigation : {r.get('mitigation','')}\n\n"

        prompt = f"""Redige UNIQUEMENT la section MATRICE DES RISQUES :

CIBLE : {state['nom_cible']}
RISQUES IDENTIFIES :
{risques_str}

Structure par niveau (critique / eleve / moyen / faible).
Pour chaque risque : titre, description courte, impact, plan de mitigation.
Termine tous les niveaux."""

        matrice = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            model=MODEL_SONNET,
        )

        partie3 = state["synthese"] + "\n\n" + matrice
        return {**state, "synthese": partie3, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur matrice risques : {str(e)}"}


def generer_verdict_final(state: DueDiligenceState) -> DueDiligenceState:
    try:
        system = """Tu es un partner senior M&A. Tu rediges en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige UNIQUEMENT la section CONDITIONS AVANT CLOSING :

CIBLE : {state['nom_cible']}
SCORE : {state['score_global']}/100

Liste 4 conditions suspensives courtes (5 lignes max chacune) :
- Condition 1 : [titre] — [description courte]
- Condition 2 : [titre] — [description courte]
- Condition 3 : [titre] — [description courte]
- Condition 4 : [titre] — [description courte]

Puis liste 3 garanties a obtenir du vendeur (3 lignes max chacune).
Termine les garanties avant de t'arreter."""

        verdict = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            model=MODEL_SONNET,
        )

        partie = state["synthese"] + "\n\n" + verdict
        return {**state, "synthese": partie, "recommandation": verdict, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur verdict : {str(e)}"}


def generer_conclusion(state: DueDiligenceState) -> DueDiligenceState:
    try:
        system = """Tu es un partner senior M&A. Tu rediges en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige UNIQUEMENT le VERDICT FINAL :

CIBLE : {state['nom_cible']}
SCORE : {state['score_global']}/100
CONTEXTE : {state['contexte']}

Structure courte et obligatoire :

DECISION : Go / No-Go / Go conditionnel (1 phrase + 2 lignes de justification)

FOURCHETTE DE VALORISATION : valeur basse — valeur recommandee — valeur haute (1 ligne chacune)

5 PROCHAINES ETAPES :
1. [action] | [responsable] | [delai]
2. [action] | [responsable] | [delai]
3. [action] | [responsable] | [delai]
4. [action] | [responsable] | [delai]
5. [action] | [responsable] | [delai]

POINTS DE BLOCAGE : 3 points maximum (1 ligne chacun)

Termine les points de blocage."""

        conclusion = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            model=MODEL_SONNET,
        )

        synthese_complete = state["synthese"] + "\n\n" + conclusion
        return {**state, "synthese": synthese_complete, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur conclusion : {str(e)}"}


def build_graph():
    graph = StateGraph(DueDiligenceState)
    graph.add_node("analyser_axes", analyser_axes)
    graph.add_node("generer_synthese_executive", generer_synthese_executive)
    graph.add_node("generer_analyse_axes", generer_analyse_axes)
    graph.add_node("generer_matrice_risques", generer_matrice_risques)
    graph.add_node("generer_verdict_final", generer_verdict_final)
    graph.add_node("generer_conclusion", generer_conclusion)

    graph.set_entry_point("analyser_axes")
    graph.add_edge("analyser_axes", "generer_synthese_executive")
    graph.add_edge("generer_synthese_executive", "generer_analyse_axes")
    graph.add_edge("generer_analyse_axes", "generer_matrice_risques")
    graph.add_edge("generer_matrice_risques", "generer_verdict_final")
    graph.add_edge("generer_verdict_final", "generer_conclusion")
    graph.add_edge("generer_conclusion", END)

    return graph.compile()