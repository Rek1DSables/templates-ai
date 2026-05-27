# graph.py
import time
import json
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    SERPER_API_KEY, SERPER_URL,
    MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class VeilleState(TypedDict):
    entreprise: str
    secteur: str
    type_veille: str
    sujets: list
    resultats_bruts: dict
    analyse: str
    niveau_alerte: str
    points_cles: list
    recommandations: str
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


def recherche_serper(query: str) -> str:
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": 5}
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        print(f"[DEBUG] Query: {query}")
        print(f"[DEBUG] Status: {response.status_code}")
        print(f"[DEBUG] Response: {response.text[:500]}")
        data = response.json()
        resultats = []
        for item in data.get("organic", [])[:5]:
            titre = item.get("title", "")
            snippet = item.get("snippet", "")
            date = item.get("date", "")
            resultats.append(f"- [{date}] {titre} : {snippet}")
        return "\n".join(resultats) if resultats else "Aucun resultat."
    except Exception as e:
        return f"Erreur recherche : {str(e)}"


def collecter_sources(state: VeilleState) -> VeilleState:
    try:
        resultats = {}
        for sujet in state["sujets"]:
            query = f"{sujet} {state['secteur']} {state['type_veille'].lower()} 2025"
            resultats[sujet] = recherche_serper(query)

        if state["type_veille"] == "Reglementaire":
            query_reg = f"reglementation loi directive {state['secteur']} 2025"
            resultats["_reglementation"] = recherche_serper(query_reg)
        elif state["type_veille"] == "Technologique":
            query_tech = f"innovation technologie IA {state['secteur']} 2025"
            resultats["_technologie"] = recherche_serper(query_tech)
        elif state["type_veille"] == "Concurrentielle":
            query_conc = f"concurrent marche {state['entreprise']} {state['secteur']} actualite"
            resultats["_marche"] = recherche_serper(query_conc)

        return {**state, "resultats_bruts": resultats, "erreur": ""}
    except Exception as e:
        return {**state, "resultats_bruts": {}, "erreur": f"Erreur collecte : {str(e)}"}


def analyser_resultats(state: VeilleState) -> VeilleState:
    try:
        system = """Tu es un analyste expert en veille strategique.
Tu analyses des resultats de recherche web et identifies les signaux importants.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "niveau_alerte": "critique|important|informatif",
  "points_cles": ["point 1", "point 2", "point 3"],
  "analyse": "analyse detaillee en 3-4 paragraphes",
  "recommandations": "3 recommandations actionnables"
}"""

        sources_str = ""
        for sujet, resultats in state["resultats_bruts"].items():
            sources_str += f"\n=== {sujet} ===\n{resultats}\n"

        prompt = f"""Analyse cette veille strategique :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Type de veille : {state['type_veille']}
Sujets surveilles : {', '.join(state['sujets'])}

Resultats collectes :
{sources_str}

Determine le niveau d'alerte et fournis une analyse complete en francais.
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

        data = json.loads(reponse_clean)

        return {
            **state,
            "niveau_alerte": data.get("niveau_alerte", "informatif"),
            "points_cles": data.get("points_cles", []),
            "analyse": data.get("analyse", ""),
            "recommandations": data.get("recommandations", ""),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse : {str(e)}"}


def generer_rapport(state: VeilleState) -> VeilleState:
    try:
        system = """Tu es un consultant en veille strategique.
Tu rediges des rapports concis, structures et actionnables en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        prompt = f"""Redige un rapport de veille strategique complet et professionnel pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Type : {state['type_veille']}
Niveau d'alerte : {state['niveau_alerte'].upper()}

Points cles :
{chr(10).join(f'- {p}' for p in state['points_cles'])}

Analyse :
{state['analyse']}

Recommandations :
{state['recommandations']}

Structure en 4 sections detaillees :
1. RESUME EXECUTIF : contexte, enjeux, conclusion principale
2. SIGNAUX DETECTES : liste des signaux identifies avec niveau d'importance
3. ANALYSE DETAILLEE : interpretation des signaux, impacts potentiels, tendances
4. RECOMMANDATIONS PRIORITAIRES : actions concretes avec responsable et delai suggere

Chaque section doit etre substantielle. Termine toujours la section 4."""

        rapport = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        return {**state, "analyse": rapport, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur rapport : {str(e)}"}


def build_graph():
    graph = StateGraph(VeilleState)
    graph.add_node("collecter_sources", collecter_sources)
    graph.add_node("analyser_resultats", analyser_resultats)
    graph.add_node("generer_rapport", generer_rapport)

    graph.set_entry_point("collecter_sources")
    graph.add_edge("collecter_sources", "analyser_resultats")
    graph.add_edge("analyser_resultats", "generer_rapport")
    graph.add_edge("generer_rapport", END)

    return graph.compile()