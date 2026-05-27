# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class RapportClientState(TypedDict):
    # Infos mission
    prestataire_nom: str
    client_nom: str
    client_entreprise: str
    type_mission: str
    periode: str
    date_rapport: str

    # Realisations
    taches_realisees: str
    kpis: str
    problemes_rencontres: str
    prochaines_etapes: str

    # Outputs
    resume_executif: str
    analyse_performance: str
    rapport_complet: str
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


def generer_resume_executif(state: RapportClientState) -> RapportClientState:
    try:
        system = """Tu es un consultant freelance expert en communication client.
Tu rediges des resumes executifs clairs, professionnels et valorisants pour le prestataire.
Tu reponds toujours en francais."""

        prompt = f"""Redige un resume executif pour ce rapport client :

Prestataire : {state['prestataire_nom']}
Client : {state['client_nom']} — {state['client_entreprise']}
Type de mission : {state['type_mission']}
Periode : {state['periode']} — {state['date_rapport']}

Taches realisees :
{state['taches_realisees']}

KPIs / Resultats :
{state['kpis']}

Le resume executif doit :
- Synthetiser les realisations cles en 3-4 phrases percutantes
- Mettre en valeur les resultats obtenus
- Etre positif et professionnel
- Donner confiance au client
- Maximum 150 mots"""

        resume = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
        )
        return {**state, "resume_executif": resume, "erreur": ""}
    except Exception as e:
        return {**state, "resume_executif": "", "erreur": f"Erreur resume : {str(e)}"}


def analyser_performance(state: RapportClientState) -> RapportClientState:
    try:
        system = """Tu es un analyste business expert en suivi de performance de missions freelance.
Tu analyses les resultats et fournis une evaluation objective et constructive.
Tu reponds toujours en francais."""

        prompt = f"""Analyse la performance de cette mission :

Type : {state['type_mission']}
Periode : {state['periode']}

KPIs et resultats :
{state['kpis']}

Problemes rencontres :
{state['problemes_rencontres']}

Fournis :
1. BILAN QUANTITATIF : chiffres cles et evolution
2. POINTS FORTS : ce qui a bien fonctionne
3. POINTS D'AMELIORATION : ce qui peut etre optimise
4. RISQUES IDENTIFIES : points de vigilance pour la suite
5. SCORE DE MISSION : X/10 avec justification"""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return {**state, "analyse_performance": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "analyse_performance": "", "erreur": f"Erreur analyse : {str(e)}"}


def rediger_rapport(state: RapportClientState) -> RapportClientState:
    try:
        system = """Tu es un expert en communication freelance client.
Tu rediges des rapports clients professionnels, clairs et valorisants.
Tu reponds en francais. Tu termines TOUJOURS toutes tes sections."""

        prompt = f"""Redige un rapport client complet et professionnel :

PRESTATAIRE : {state['prestataire_nom']}
CLIENT : {state['client_nom']} — {state['client_entreprise']}
MISSION : {state['type_mission']}
PERIODE : {state['periode']} — {state['date_rapport']}

RESUME EXECUTIF :
{state['resume_executif']}

TACHES REALISEES :
{state['taches_realisees']}

KPIs :
{state['kpis']}

ANALYSE PERFORMANCE :
{state['analyse_performance']}

PROBLEMES RENCONTRES :
{state['problemes_rencontres']}

PROCHAINES ETAPES :
{state['prochaines_etapes']}

Structure le rapport avec ces sections :
1. RESUME EXECUTIF
2. REALISATIONS DE LA PERIODE
3. RESULTATS ET KPIs
4. ANALYSE DE PERFORMANCE
5. POINTS D'ATTENTION
6. PROCHAINES ETAPES ET OBJECTIFS
7. CONCLUSION ET RECOMMANDATIONS

Style : professionnel, valorisant, oriente resultats.
Chaque section doit etre substantielle et apporter de la valeur."""

        rapport = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )
        return {**state, "rapport_complet": rapport, "erreur": ""}
    except Exception as e:
        return {**state, "rapport_complet": "", "erreur": f"Erreur rapport : {str(e)}"}


def build_graph():
    graph = StateGraph(RapportClientState)
    graph.add_node("generer_resume_executif", generer_resume_executif)
    graph.add_node("analyser_performance", analyser_performance)
    graph.add_node("rediger_rapport", rediger_rapport)

    graph.set_entry_point("generer_resume_executif")
    graph.add_edge("generer_resume_executif", "analyser_performance")
    graph.add_edge("analyser_performance", "rediger_rapport")
    graph.add_edge("rediger_rapport", END)

    return graph.compile()