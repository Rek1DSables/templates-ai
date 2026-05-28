# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class PropaleState(TypedDict):
    prestataire_nom: str
    prestataire_email: str
    prestataire_expertise: str
    client_nom: str
    client_entreprise: str
    client_secteur: str
    client_email: str
    type_mission: str
    description_besoin: str
    objectifs: str
    budget: str
    delai: str
    mode_facturation: str
    analyse_besoin: str
    solution_proposee: str
    propale_complete: str
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


def analyser_besoin(state: PropaleState) -> PropaleState:
    try:
        system = """Tu es un consultant senior expert en transformation digitale et AI.
Tu analyses les besoins client avec precision et identifies les enjeux cles.
Tu reponds toujours en francais avec un style professionnel."""

        prompt = f"""Analyse ce besoin client :

Client : {state['client_nom']} — {state['client_entreprise']} ({state['client_secteur']})
Type de mission : {state['type_mission']}
Description du besoin : {state['description_besoin']}
Objectifs : {state['objectifs']}
Budget : {state['budget']}
Delai : {state['delai']}

Fournis une analyse en 3 points :
1. ENJEUX : les vrais enjeux business derriere ce besoin
2. COMPLEXITE : evaluation de la complexite technique et organisationnelle
3. FACTEURS CLES DE SUCCES : ce qui determinera le succes de la mission"""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return {**state, "analyse_besoin": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "analyse_besoin": "", "erreur": f"Erreur analyse : {str(e)}"}


def construire_solution(state: PropaleState) -> PropaleState:
    try:
        system = """Tu es un architect de solutions digitales expert.
Tu construis des solutions techniques adaptees aux besoins client.
Tu reponds toujours en francais avec un style professionnel et concret."""

        prompt = f"""Construis la solution pour cette mission :

Type : {state['type_mission']}
Besoin : {state['description_besoin']}
Objectifs : {state['objectifs']}
Budget : {state['budget']}
Delai : {state['delai']}
Mode : {state['mode_facturation']}
Expertise prestataire : {state['prestataire_expertise']}

Analyse du besoin :
{state['analyse_besoin']}

Decris :
1. SOLUTION PROPOSEE : description technique et fonctionnelle
2. LIVRABLES : liste precise de ce qui sera livre
3. TECHNOLOGIES : stack technique utilise
4. PLANNING : decoupage en phases avec durees"""

        solution = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )
        return {**state, "solution_proposee": solution, "erreur": ""}
    except Exception as e:
        return {**state, "solution_proposee": "", "erreur": f"Erreur solution : {str(e)}"}


def rediger_propale_partie1(state: PropaleState) -> PropaleState:
    try:
        system = """Tu es un expert en redaction de propositions commerciales.
Tu rediges des propales professionnelles, convaincantes et structurees en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        prompt = f"""Redige les sections 1 a 4 de cette proposition commerciale :

PRESTATAIRE : {state['prestataire_nom']} ({state['prestataire_email']})
CLIENT : {state['client_nom']} — {state['client_entreprise']}
MISSION : {state['type_mission']}
BUDGET : {state['budget']}
DELAI : {state['delai']}
MODE : {state['mode_facturation']}

ANALYSE DU BESOIN :
{state['analyse_besoin']}

SOLUTION :
{state['solution_proposee']}

Sections a rediger :
1. CONTEXTE ET COMPREHENSION DU BESOIN
2. NOTRE APPROCHE ET SOLUTION
3. LIVRABLES ET PLANNING
4. INVESTISSEMENT ({state['mode_facturation']} — {state['budget']})

Style professionnel, concis, oriente resultats. Termine imperativement la section 4."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return {**state, "propale_complete": response.content[0].text, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur propale partie 1 : {str(e)}"}


def rediger_propale_partie2(state: PropaleState) -> PropaleState:
    try:
        system = """Tu es un expert en redaction de propositions commerciales.
Tu rediges des propales professionnelles en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        prompt = f"""Redige les sections 5 a 7 de cette proposition commerciale :

PRESTATAIRE : {state['prestataire_nom']}
CLIENT : {state['client_nom']} — {state['client_entreprise']}
MISSION : {state['type_mission']}
BUDGET : {state['budget']}

Sections a rediger :
5. POURQUOI NOUS CHOISIR
6. PROCHAINES ETAPES
7. CONDITIONS GENERALES (paiement, confidentialite, propriete intellectuelle)

Style professionnel. Termine IMPERATIVEMENT la section 7."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        propale_complete = state["propale_complete"] + "\n\n" + response.content[0].text
        return {**state, "propale_complete": propale_complete, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur propale partie 2 : {str(e)}"}


def build_graph():
    graph = StateGraph(PropaleState)
    graph.add_node("analyser_besoin", analyser_besoin)
    graph.add_node("construire_solution", construire_solution)
    graph.add_node("rediger_propale_partie1", rediger_propale_partie1)
    graph.add_node("rediger_propale_partie2", rediger_propale_partie2)

    graph.set_entry_point("analyser_besoin")
    graph.add_edge("analyser_besoin", "construire_solution")
    graph.add_edge("construire_solution", "rediger_propale_partie1")
    graph.add_edge("rediger_propale_partie1", "rediger_propale_partie2")
    graph.add_edge("rediger_propale_partie2", END)

    return graph.compile()