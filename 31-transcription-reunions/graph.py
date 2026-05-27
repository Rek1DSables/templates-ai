# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ReunionState(TypedDict):
    titre: str
    date_reunion: str
    participants: str
    transcript_brut: str
    transcript_nettoye: str
    resume: str
    action_items: str
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
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surchargé, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def nettoyer_transcript(state: ReunionState) -> ReunionState:
    try:
        system = (
            "Tu es un assistant specialise dans le traitement de transcriptions de reunions. "
            "Tu nettoies et structures les transcriptions brutes pour les rendre lisibles. "
            "Tu corriges les fautes, supprimes les repetitions et identifies les intervenants."
        )
        prompt = f"""Nettoie et structure cette transcription de reunion :

TITRE : {state['titre']}
DATE : {state['date_reunion']}
PARTICIPANTS : {state['participants']}

TRANSCRIPT BRUT :
{state['transcript_brut']}

Retourne la transcription nettoyee et structuree avec :
- Les intervenants clairement identifies (format Prenom : texte)
- Les repetitions et hesitations supprimees
- La ponctuation corrigee
- Les paragraphes bien separes"""

        nettoye = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "transcript_nettoye": nettoye, "erreur": ""}
    except Exception as e:
        return {**state, "transcript_nettoye": "", "erreur": f"Erreur nettoyage : {str(e)}"}


def generer_resume(state: ReunionState) -> ReunionState:
    try:
        system = (
            "Tu es un assistant specialise dans la synthese de reunions professionnelles. "
            "Tu produis des resumes executes clairs, structures et actionables. "
            "Tu vas a l'essentiel sans perdre d'information critique."
        )
        prompt = f"""Redige un resume executif de cette reunion :

TITRE : {state['titre']}
DATE : {state['date_reunion']}
PARTICIPANTS : {state['participants']}

TRANSCRIPT :
{state['transcript_nettoye'] or state['transcript_brut']}

Le resume doit inclure :
1. CONTEXTE (2-3 phrases sur l'objet de la reunion)
2. POINTS CLES DISCUTES (liste des sujets abordes)
3. DECISIONS PRISES (decisions actees pendant la reunion)
4. POINTS EN SUSPENS (sujets non resolus a suivre)
5. PROCHAINE ETAPE (si mentionnee)"""

        resume = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "resume": resume, "erreur": ""}
    except Exception as e:
        return {**state, "resume": "", "erreur": f"Erreur resume : {str(e)}"}


def extraire_action_items(state: ReunionState) -> ReunionState:
    try:
        system = (
            "Tu es un assistant specialise dans l'extraction de taches et actions. "
            "Tu identifies avec precision les action items, leurs responsables et deadlines. "
            "Tu es exhaustif et ne manques aucune tache mentionnee."
        )
        prompt = f"""Extrait tous les action items de cette reunion :

TITRE : {state['titre']}
PARTICIPANTS : {state['participants']}

TRANSCRIPT :
{state['transcript_nettoye'] or state['transcript_brut']}

Pour chaque action item, indique :
- [ ] ACTION : description precise de la tache
  RESPONSABLE : nom de la personne en charge
  DEADLINE : date ou delai mentionne (ou "Non precise")
  PRIORITE : Haute / Moyenne / Basse

Classe les action items par priorite decroissante."""

        actions = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "action_items": actions, "erreur": ""}
    except Exception as e:
        return {**state, "action_items": "", "erreur": f"Erreur action items : {str(e)}"}


def build_graph():
    graph = StateGraph(ReunionState)
    graph.add_node("nettoyer_transcript", nettoyer_transcript)
    graph.add_node("generer_resume", generer_resume)
    graph.add_node("extraire_action_items", extraire_action_items)

    graph.set_entry_point("nettoyer_transcript")
    graph.add_edge("nettoyer_transcript", "generer_resume")
    graph.add_edge("generer_resume", "extraire_action_items")
    graph.add_edge("extraire_action_items", END)

    return graph.compile()