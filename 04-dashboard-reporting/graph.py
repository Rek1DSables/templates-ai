# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ReportingState(TypedDict):
    entreprise: str
    secteur: str
    periode: str
    kpis: dict
    analyse_kpis: str
    tendances: list
    alertes: list
    recommandations: str
    score_sante: int
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


def analyser_kpis(state: ReportingState) -> ReportingState:
    try:
        system = """Tu es un analyste business expert en performance et KPIs.
Tu analyses des indicateurs de performance et identifies les tendances et alertes.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "analyse": "analyse globale en 2-3 paragraphes",
  "tendances": ["tendance 1", "tendance 2", "tendance 3"],
  "alertes": ["alerte 1", "alerte 2"],
  "score_sante": 75
}
Le score_sante est entre 0 et 100."""

        kpis_str = "\n".join([f"- {k} : {v}" for k, v in state["kpis"].items()])

        prompt = f"""Analyse ces KPIs business :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Periode : {state['periode']}

KPIs :
{kpis_str}

Fournis une analyse complete avec tendances, alertes et score de sante global.
Reponds uniquement avec le JSON."""

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

        data = json.loads(reponse_clean)

        return {
            **state,
            "analyse_kpis": data.get("analyse", ""),
            "tendances": data.get("tendances", []),
            "alertes": data.get("alertes", []),
            "score_sante": int(data.get("score_sante", 50)),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def generer_recommandations(state: ReportingState) -> ReportingState:
    try:
        system = """Tu es un consultant business senior.
Tu generes des recommandations concretes et actionnables basees sur l'analyse des KPIs.
Tu reponds toujours en francais avec un style professionnel.
Tu termines TOUJOURS toutes tes recommandations avant de t'arreter."""

        kpis_str = "\n".join([f"- {k} : {v}" for k, v in state["kpis"].items()])

        prompt = f"""Genere des recommandations strategiques pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Periode : {state['periode']}
Score de sante : {state['score_sante']}/100

KPIs :
{kpis_str}

Tendances detectees :
{chr(10).join(f'- {t}' for t in state['tendances'])}

Alertes :
{chr(10).join(f'- {a}' for a in state['alertes'])}

Genere 5 recommandations prioritaires avec pour chacune :
- ACTION CONCRETE : description precise de l'action
- IMPACT ATTENDU : resultat mesurable vise
- DELAI : court terme (< 1 mois) / moyen terme (1-3 mois) / long terme (3-6 mois)
- RESPONSABLE : profil en charge
- KPI DE SUIVI : indicateur pour mesurer le succes"""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        recommandations = response.content[0].text
        return {**state, "recommandations": recommandations, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur recommandations : {str(e)}"}


def build_graph():
    graph = StateGraph(ReportingState)
    graph.add_node("analyser_kpis", analyser_kpis)
    graph.add_node("generer_recommandations", generer_recommandations)

    graph.set_entry_point("analyser_kpis")
    graph.add_edge("analyser_kpis", "generer_recommandations")
    graph.add_edge("generer_recommandations", END)

    return graph.compile()