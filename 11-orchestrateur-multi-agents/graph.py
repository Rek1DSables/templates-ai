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
    MAX_SOUS_TACHES, MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class OrchestratorState(TypedDict):
    tache: str
    sous_taches: list
    resultats_agents: dict
    synthese: str
    erreur: str


def invoke_with_retry(messages: list, system: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2000,
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
        return "\n".join(resultats) if resultats else "Aucun resultat."
    except Exception as e:
        return f"Erreur recherche : {str(e)}"


def orchestrer(state: OrchestratorState) -> OrchestratorState:
    try:
        system = """Tu es un orchestrateur d'agents AI. Tu recois une tache complexe et tu la decompose en sous-taches specialisees.

Reponds UNIQUEMENT avec un JSON valide, sans texte autour, sans backticks :
{
  "sous_taches": [
    {"id": "1", "agent": "recherche", "instruction": "..."},
    {"id": "2", "agent": "analyse", "instruction": "..."},
    {"id": "3", "agent": "redaction", "instruction": "..."},
    {"id": "4", "agent": "synthese", "instruction": "..."}
  ]
}

Agents disponibles :
- recherche : cherche des informations sur le web
- analyse : analyse des donnees ou informations fournies
- redaction : redige du contenu structure
- synthese : synthetise et consolide des informations

Maximum 4 sous-taches. Chaque instruction doit etre precise et actionnable."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Tache a decomposer : {state['tache']}"}],
        )

        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)
        sous_taches = data.get("sous_taches", [])[:MAX_SOUS_TACHES]

        return {**state, "sous_taches": sous_taches, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur orchestration : {str(e)}"}


def agent_recherche(instruction: str) -> str:
    try:
        system = "Tu es un agent de recherche. Tu cherches des informations pertinentes sur le web et tu synthetises les resultats en francais."
        query_reponse = invoke_with_retry(
            system="Tu generes une requete de recherche courte et precise en anglais pour trouver : " + instruction,
            messages=[{"role": "user", "content": instruction}],
        )
        resultats = recherche_web(query_reponse.strip())
        synthese = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Instruction : {instruction}\n\nResultats bruts :\n{resultats}\n\nSynthetise en francais."}],
        )
        return synthese
    except Exception as e:
        return f"Erreur agent recherche : {str(e)}"


def agent_analyse(instruction: str, contexte: str) -> str:
    try:
        system = "Tu es un agent d'analyse expert. Tu analyses des informations et fournis des insights structures et actionnables en francais."
        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Instruction : {instruction}\n\nContexte disponible :\n{contexte}\n\nFournis une analyse detaillee en francais."}],
        )
        return reponse
    except Exception as e:
        return f"Erreur agent analyse : {str(e)}"


def agent_redaction(instruction: str, contexte: str) -> str:
    try:
        system = "Tu es un agent de redaction expert. Tu rediges du contenu professionnel, structure et clair en francais."
        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Instruction : {instruction}\n\nContexte disponible :\n{contexte}\n\nRedige le contenu demande en francais."}],
        )
        return reponse
    except Exception as e:
        return f"Erreur agent redaction : {str(e)}"


def agent_synthese(instruction: str, contexte: str) -> str:
    try:
        system = "Tu es un agent de synthese expert. Tu consolides et structures des informations complexes en un output clair et actionnable en francais."
        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Instruction : {instruction}\n\nInformations a synthetiser :\n{contexte}\n\nFournis une synthese complete en francais."}],
        )
        return reponse
    except Exception as e:
        return f"Erreur agent synthese : {str(e)}"


def dispatcher(state: OrchestratorState) -> OrchestratorState:
    try:
        resultats = {}
        contexte_cumule = f"Tache principale : {state['tache']}\n\n"

        for sous_tache in state["sous_taches"]:
            agent = sous_tache.get("agent", "")
            instruction = sous_tache.get("instruction", "")
            id_tache = sous_tache.get("id", "")

            if agent == "recherche":
                resultat = agent_recherche(instruction)
            elif agent == "analyse":
                resultat = agent_analyse(instruction, contexte_cumule)
            elif agent == "redaction":
                resultat = agent_redaction(instruction, contexte_cumule)
            elif agent == "synthese":
                resultat = agent_synthese(instruction, contexte_cumule)
            else:
                resultat = f"Agent inconnu : {agent}"

            resultats[id_tache] = {
                "agent": agent,
                "instruction": instruction,
                "resultat": resultat,
            }
            contexte_cumule += f"\n--- Resultat agent {agent} (tache {id_tache}) ---\n{resultat}\n"

        return {**state, "resultats_agents": resultats, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur dispatcher : {str(e)}"}


def agregateur(state: OrchestratorState) -> OrchestratorState:
    try:
        contexte = f"Tache originale : {state['tache']}\n\n"
        for id_tache, data in state["resultats_agents"].items():
            # Tronquer chaque resultat a 1000 caracteres pour eviter overflow
            resultat_tronque = data['resultat'][:1000] + "..." if len(data['resultat']) > 1000 else data['resultat']
            contexte += f"=== Agent {data['agent'].upper()} ===\n"
            contexte += f"Instruction : {data['instruction']}\n"
            contexte += f"Resultat : {resultat_tronque}\n\n"

        system = (
            "Tu es un orchestrateur AI. Tu agrege les resultats de plusieurs agents specialises "
            "en une livrable finale complete, structuree et professionnelle en francais. "
            "Tu termines TOUJOURS toutes tes sections avant de t'arreter."
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            messages=[{
                "role": "user",
                "content": f"{contexte}\n\nAggrege tous ces resultats en une livrable finale complete, structuree et directement utilisable en francais. Termine toujours par une conclusion."
            }],
        )
        synthese = response.content[0].text
        return {**state, "synthese": synthese, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur agregation : {str(e)}"}


def build_graph():
    graph = StateGraph(OrchestratorState)
    graph.add_node("orchestrer", orchestrer)
    graph.add_node("dispatcher", dispatcher)
    graph.add_node("agregateur", agregateur)

    graph.set_entry_point("orchestrer")
    graph.add_edge("orchestrer", "dispatcher")
    graph.add_edge("dispatcher", "agregateur")
    graph.add_edge("agregateur", END)

    return graph.compile()