# graph.py
import time
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    SERPER_API_KEY, SERPER_URL,
    MAX_ITERATIONS, MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ReactState(TypedDict):
    question: str
    historique: list
    iteration: int
    pensee: str
    action: str
    observation: str
    reponse_finale: str
    erreur: str


def invoke_with_retry(messages: list, system: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1500,
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


def recherche_web(query: str) -> str:
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": 5}
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        data = response.json()
        resultats = []
        for item in data.get("organic", [])[:5]:
            titre = item.get("title", "")
            snippet = item.get("snippet", "")
            resultats.append(f"- {titre} : {snippet}")
        return "\n".join(resultats) if resultats else "Aucun resultat trouve."
    except Exception as e:
        return f"Erreur recherche : {str(e)}"


def raisonner(state: ReactState) -> ReactState:
    try:
        system = """Tu es un agent de recherche autonome qui utilise le pattern ReAct.

Pour chaque etape, reponds EXACTEMENT dans ce format :

PENSEE: [ton raisonnement]
ACTION: [soit "recherche: ta requete" soit "reponse_finale: ta reponse"]

Regles :
- ACTION: recherche: pour chercher des informations
- ACTION: reponse_finale: quand tu as assez d'informations
- Les requetes de recherche doivent etre en anglais pour de meilleurs resultats"""

        historique_str = "\n".join(state["historique"]) if state["historique"] else "Aucune etape precedente."

        messages = [
            {
                "role": "user",
                "content": f"""Question : {state['question']}

Historique :
{historique_str}

Iteration : {state['iteration'] + 1}/{MAX_ITERATIONS}

Que fais-tu ?"""
            }
        ]

        reponse = invoke_with_retry(messages=messages, system=system)

        pensee = ""
        action = ""

        for ligne in reponse.split("\n"):
            if ligne.startswith("PENSEE:"):
                pensee = ligne.replace("PENSEE:", "").strip()
            elif ligne.startswith("ACTION:"):
                action = ligne.replace("ACTION:", "").strip()

        if not action:
            action = "reponse_finale: " + reponse

        return {**state, "pensee": pensee, "action": action, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur raisonnement : {str(e)}"}


def agir(state: ReactState) -> ReactState:
    try:
        action = state["action"]
        historique = list(state["historique"])

        historique.append(f"PENSEE: {state['pensee']}")
        historique.append(f"ACTION: {action}")

        if action.startswith("recherche:"):
            query = action.replace("recherche:", "").strip()
            observation = recherche_web(query)
            historique.append(f"OBSERVATION: {observation}")
            return {
                **state,
                "observation": observation,
                "historique": historique,
                "iteration": state["iteration"] + 1,
                "reponse_finale": "",
            }

        elif action.startswith("reponse_finale:"):
            reponse = action.replace("reponse_finale:", "").strip()
            historique.append(f"REPONSE FINALE: {reponse}")
            return {
                **state,
                "reponse_finale": reponse,
                "historique": historique,
                "iteration": state["iteration"] + 1,
            }

        else:
            return {
                **state,
                "reponse_finale": action,
                "historique": historique,
                "iteration": state["iteration"] + 1,
            }

    except Exception as e:
        return {**state, "erreur": f"Erreur action : {str(e)}"}


def traduire_reponse(state: ReactState) -> ReactState:
    if not state.get("reponse_finale"):
        return state
    try:
        reponse = invoke_with_retry(
            system="Tu es un traducteur expert. Traduis le texte suivant en francais. Ne modifie pas le contenu, traduis uniquement. Si le texte est deja en francais, retourne-le tel quel.",
            messages=[{"role": "user", "content": state["reponse_finale"]}],
        )
        return {**state, "reponse_finale": reponse}
    except Exception as e:
        return {**state, "erreur": f"Erreur traduction : {str(e)}"}


def doit_continuer(state: ReactState) -> str:
    if state.get("erreur"):
        return "fin"
    if state.get("reponse_finale"):
        return "fin"
    if state["iteration"] >= MAX_ITERATIONS:
        return "fin"
    return "continuer"


def build_graph():
    graph = StateGraph(ReactState)
    graph.add_node("raisonner", raisonner)
    graph.add_node("agir", agir)
    graph.add_node("traduire_reponse", traduire_reponse)

    graph.set_entry_point("raisonner")
    graph.add_edge("raisonner", "agir")
    graph.add_conditional_edges(
        "agir",
        doit_continuer,
        {
            "continuer": "raisonner",
            "fin": "traduire_reponse",
        }
    )
    graph.add_edge("traduire_reponse", END)

    return graph.compile()