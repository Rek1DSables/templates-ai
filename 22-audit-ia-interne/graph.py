# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class AuditState(TypedDict):
    entreprise: str
    secteur: str
    taille: str
    budget_ia: str
    processus: str
    analyse_processus: str
    opportunites: list
    roadmap: str
    score_global: int
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 4096) -> str:
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


def analyser_processus(state: AuditState) -> AuditState:
    try:
        system = """Tu es un expert en transformation digitale et automatisation IA.
Tu analyses les processus d'une entreprise avec un regard critique et structure.
Tu reponds toujours en francais. Sois concis et factuel."""

        prompt = f"""Analyse les processus de cette entreprise :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Taille : {state['taille']}
Budget IA envisage : {state['budget_ia']}

Processus actuels :
{state['processus']}

Fournis une analyse couvrant ces 5 points, 2-3 lignes chacun :
1. CARTOGRAPHIE : liste des processus identifies
2. MATURITE DIGITALE : niveau actuel (1-5) et justification
3. POINTS DE FRICTION : principaux goulots d'etranglement
4. VOLUME : estimation des taches repetitives
5. DONNEES : qualite et accessibilite pour l'IA"""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )

        return {**state, "analyse_processus": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "analyse_processus": "", "erreur": f"Erreur analyse : {str(e)}"}


def identifier_opportunites(state: AuditState) -> AuditState:
    try:
        system = """Tu es un expert en automatisation IA specialise dans l'identification d'opportunites ROI.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks ni texte autour.
Format :
[
  {
    "processus": "nom",
    "tache": "description courte",
    "score_automatisabilite": 8,
    "gain_temps_heures_semaine": 10,
    "complexite_implementation": "faible|moyenne|elevee",
    "delai_implementation_semaines": 4,
    "roi_estime_mois": 6,
    "technologie_recommandee": "LangGraph + Claude",
    "priorite": "haute|moyenne|basse"
  }
]"""

        prompt = f"""Identifie 4 a 6 opportunites d'automatisation IA pour :

Secteur : {state['secteur']}
Taille : {state['taille']}
Budget : {state['budget_ia']}

Processus :
{state['processus']}

Analyse :
{state['analyse_processus']}

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

        opportunites = json.loads(reponse_clean)
        score_global = int(sum(o.get("score_automatisabilite", 5) for o in opportunites) / len(opportunites)) if opportunites else 5

        return {**state, "opportunites": opportunites, "score_global": score_global, "erreur": ""}
    except Exception as e:
        return {**state, "opportunites": [], "score_global": 0, "erreur": f"Erreur opportunites : {str(e)}"}


def generer_roadmap(state: AuditState) -> AuditState:
    try:
        system = """Tu es un consultant senior en transformation IA.
Tu generes des roadmaps concis, realistes et priorises par ROI.
Tu reponds en francais. Tu adaptes la longueur au sujet sans remplissage.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        opportunites_str = json.dumps(state["opportunites"], ensure_ascii=False, indent=2)

        prompt = f"""Genere un roadmap IA pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Taille : {state['taille']}
Budget : {state['budget_ia']}
Score automatisabilite : {state['score_global']}/10

Opportunites :
{opportunites_str}

Structure en 6 sections avec bullets concis :
1. SYNTHESE EXECUTIVE (3 points cles)
2. PHASE 1 QUICK WINS 0-3 mois (3 actions)
3. PHASE 2 CONSOLIDATION 3-6 mois (2-3 projets)
4. PHASE 3 TRANSFORMATION 6-12 mois (2 projets)
5. BUDGET PAR PHASE (1 ligne par phase)
6. PROCHAINES ETAPES (3 actions cette semaine)

Regles :
- Bullets courts, pas de phrases longues
- Pas de sous-sections inutiles
- Ne commence pas une section que tu ne peux pas terminer
- La section 6 PROCHAINES ETAPES est obligatoire et doit etre complete"""

        roadmap = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        return {**state, "roadmap": roadmap, "erreur": ""}
    except Exception as e:
        return {**state, "roadmap": "", "erreur": f"Erreur roadmap : {str(e)}"}


def build_graph():
    graph = StateGraph(AuditState)
    graph.add_node("analyser_processus", analyser_processus)
    graph.add_node("identifier_opportunites", identifier_opportunites)
    graph.add_node("generer_roadmap", generer_roadmap)

    graph.set_entry_point("analyser_processus")
    graph.add_edge("analyser_processus", "identifier_opportunites")
    graph.add_edge("identifier_opportunites", "generer_roadmap")
    graph.add_edge("generer_roadmap", END)

    return graph.compile()