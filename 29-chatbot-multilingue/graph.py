# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ChatbotState(TypedDict):
    message_utilisateur: str
    historique: list
    base_connaissance: str
    langue_detectee: str
    reponse: str
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 1000) -> str:
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


def detecter_langue(state: ChatbotState) -> ChatbotState:
    try:
        system = """Tu es un detecteur de langue. Tu identifies la langue d'un texte.
Tu reponds UNIQUEMENT avec le nom de la langue en francais, rien d'autre.
Exemples : Français, English, Español, Deutsch, Italiano, Português, 中文, 日本語, العربية"""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Quelle est la langue de ce texte : {state['message_utilisateur']}"}],
            max_tokens=20,
        )
        return {**state, "langue_detectee": reponse.strip(), "erreur": ""}
    except Exception as e:
        return {**state, "langue_detectee": "Français", "erreur": f"Erreur detection : {str(e)}"}


def generer_reponse(state: ChatbotState) -> ChatbotState:
    try:
        system = f"""Tu es un assistant client professionnel et bienveillant.
Tu reponds TOUJOURS dans la langue de l'utilisateur : {state['langue_detectee']}.
Tu utilises uniquement les informations de la base de connaissance pour repondre.
Si tu ne connais pas la reponse, tu le dis poliment et tu proposes de contacter le support.
Tu es concis, clair et utile.

BASE DE CONNAISSANCE :
{state['base_connaissance']}"""

        # Construction de l'historique
        messages = []
        for echange in state["historique"]:
            messages.append({"role": "user", "content": echange["user"]})
            messages.append({"role": "assistant", "content": echange["assistant"]})
        messages.append({"role": "user", "content": state["message_utilisateur"]})

        reponse = invoke_with_retry(
            system=system,
            messages=messages,
            max_tokens=800,
        )
        return {**state, "reponse": reponse, "erreur": ""}
    except Exception as e:
        return {**state, "reponse": "", "erreur": f"Erreur reponse : {str(e)}"}


def build_graph():
    graph = StateGraph(ChatbotState)
    graph.add_node("detecter_langue", detecter_langue)
    graph.add_node("generer_reponse", generer_reponse)

    graph.set_entry_point("detecter_langue")
    graph.add_edge("detecter_langue", "generer_reponse")
    graph.add_edge("generer_reponse", END)

    return graph.compile()