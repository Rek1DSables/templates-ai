# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContratState(TypedDict):
    type_contrat: str
    freelance_nom: str
    freelance_email: str
    client_nom: str
    client_email: str
    prestation: str
    tarif: str
    duree: str
    date_debut: str
    contenu_genere: str
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
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modèle surchargé, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def generer_contrat(state: ContratState) -> ContratState:
    try:
        system = (
            "Tu es un assistant juridique spécialisé dans la rédaction de contrats freelance français. "
            "Tu rédiges des contrats professionnels, clairs et complets. "
            "Tu utilises un langage juridique adapté mais accessible. "
            "Tu structures toujours le contrat avec des articles numérotés."
        )

        prompt = f"""Rédige un contrat de {state['type_contrat']} complet et professionnel avec les informations suivantes :

PRESTATAIRE :
- Nom : {state['freelance_nom']}
- Email : {state['freelance_email']}

CLIENT :
- Nom : {state['client_nom']}
- Email : {state['client_email']}

MISSION :
- Description : {state['prestation']}
- Tarif : {state['tarif']}
- Durée : {state['duree']}
- Date de début : {state['date_debut']}

Le contrat doit inclure :
Article 1 — Objet du contrat
Article 2 — Durée et dates
Article 3 — Description détaillée des prestations
Article 4 — Tarifs et modalités de paiement
Article 5 — Obligations du prestataire
Article 6 — Obligations du client
Article 7 — Confidentialité
Article 8 — Propriété intellectuelle
Article 9 — Résiliation
Article 10 — Litiges et droit applicable

Termine par un bloc signature avec date, lieu et espaces pour les deux parties."""

        contenu = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )

        return {**state, "contenu_genere": contenu, "erreur": ""}

    except Exception as e:
        return {**state, "contenu_genere": "", "erreur": f"Erreur génération : {str(e)}"}


def build_graph():
    graph = StateGraph(ContratState)
    graph.add_node("generer_contrat", generer_contrat)
    graph.set_entry_point("generer_contrat")
    graph.add_edge("generer_contrat", END)
    return graph.compile()