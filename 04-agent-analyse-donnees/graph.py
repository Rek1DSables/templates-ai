# graph.py
import time
import json
import anthropic
import pandas as pd
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class AnalyseState(TypedDict):
    type_analyse: str
    nom_fichier: str
    contexte: str
    donnees_brutes: str
    statistiques: dict
    insights: str
    recommandations: str
    alertes: list
    visualisations: list
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


def analyser_structure(state: AnalyseState) -> AnalyseState:
    try:
        system = """Tu es un data analyst expert.
Tu analyses la structure et les statistiques d'un dataset.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "nb_lignes": 0,
  "nb_colonnes": 0,
  "colonnes": [{"nom": "", "type": "", "valeurs_manquantes": 0, "description": ""}],
  "statistiques_cles": {"col": {"min": 0, "max": 0, "moyenne": 0, "mediane": 0}},
  "qualite_donnees": 85,
  "alertes": ["alerte 1", "alerte 2"]
}"""

        prompt = f"""Analyse la structure de ce dataset :

Nom fichier : {state['nom_fichier']}
Type d'analyse demandé : {state['type_analyse']}
Contexte : {state['contexte']}

DONNEES (extrait) :
{state['donnees_brutes'][:3000]}

Reponds uniquement avec le JSON."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        stats = json.loads(reponse_clean)
        return {
            **state,
            "statistiques": stats,
            "alertes": stats.get("alertes", []),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "statistiques": {}, "erreur": f"Erreur analyse structure : {str(e)}"}


def generer_insights(state: AnalyseState) -> AnalyseState:
    try:
        system = """Tu es un data analyst senior et consultant business.
Tu generes des insights actionnables depuis des donnees.
Tu reponds toujours en francais avec un style professionnel.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        stats_str = json.dumps(state["statistiques"], ensure_ascii=False, indent=2)

        prompt = f"""Genere des insights business depuis cette analyse de donnees :

Type d'analyse : {state['type_analyse']}
Contexte : {state['contexte']}
Fichier : {state['nom_fichier']}

STATISTIQUES :
{stats_str}

DONNEES (extrait) :
{state['donnees_brutes'][:2000]}

Redige :

1. SYNTHESE EXECUTIVE (3-4 points cles)
   - Ce que les donnees revelent en priorite
   - Chiffres les plus significatifs

2. INSIGHTS DETAILLES (5-7 insights)
   - Chaque insight avec : observation + interpretation + impact business

3. ANOMALIES ET RISQUES
   - Points atypiques identifies
   - Donnees manquantes ou suspectes

4. RECOMMANDATIONS ACTIONNABLES (5 recommandations)
   - Action concrete + impact attendu + priorite

Sois precis, chiffre tes observations, reste actionnable."""

        insights = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            model=MODEL_SONNET,
        )

        return {**state, "insights": insights, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur insights : {str(e)}"}


def generer_insights_suite(state: AnalyseState) -> AnalyseState:
    try:
        system = """Tu es un data analyst senior et consultant business.
Tu completes une analyse de donnees en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        prompt = f"""Continue et termine cette analyse de donnees :

Type : {state['type_analyse']}
Contexte : {state['contexte']}

ANALYSE EN COURS :
{state['insights'][-500:]}

Redige uniquement les sections manquantes parmi :
- ANOMALIES ET RISQUES (si pas encore faite)
- RECOMMANDATIONS ACTIONNABLES avec 5 recommandations chiffrees (priorite haute / moyenne / basse)

Termine IMPERATIVEMENT les recommandations avant de t'arreter."""

        suite = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            model=MODEL_SONNET,
        )

        insights_complet = state["insights"] + "\n\n" + suite
        return {**state, "insights": insights_complet, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur insights suite : {str(e)}"}


def build_graph():
    graph = StateGraph(AnalyseState)
    graph.add_node("analyser_structure", analyser_structure)
    graph.add_node("generer_insights", generer_insights)
    graph.add_node("generer_insights_suite", generer_insights_suite)

    graph.set_entry_point("analyser_structure")
    graph.add_edge("analyser_structure", "generer_insights")
    graph.add_edge("generer_insights", "generer_insights_suite")
    graph.add_edge("generer_insights_suite", END)

    return graph.compile()