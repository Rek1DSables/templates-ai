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


def generer_roadmap_partie1(state: AuditState) -> AuditState:
    try:
        system = """Tu es un consultant senior en transformation IA.
Tu rediges des roadmaps professionnels, detailles et priorises par ROI en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        opportunites_courtes = []
        for o in state["opportunites"]:
            opportunites_courtes.append({
                "tache": o.get("tache", ""),
                "score_automatisabilite": o.get("score_automatisabilite", ""),
                "gain_temps_heures_semaine": o.get("gain_temps_heures_semaine", ""),
                "roi_estime_mois": o.get("roi_estime_mois", ""),
                "priorite": o.get("priorite", ""),
                "technologie_recommandee": o.get("technologie_recommandee", ""),
            })
        opportunites_str = json.dumps(opportunites_courtes, ensure_ascii=False, indent=2)

        prompt = f"""Redige les sections 1 a 4 du roadmap IA pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Taille : {state['taille']}
Budget IA : {state['budget_ia']}
Score global d'automatisabilite : {state['score_global']}/10

Opportunites identifiees :
{opportunites_str}

Redige ces 4 sections de facon detaillee et professionnelle :
1. SYNTHESE EXECUTIVE : bilan de l'audit en 5 points cles
2. PHASE 1 QUICK WINS (0-3 mois) : 3 actions a fort ROI avec budget et gain temps
3. PHASE 2 CONSOLIDATION (3-6 mois) : 2-3 projets a complexite moyenne
4. PHASE 3 TRANSFORMATION (6-12 mois) : 2 projets strategiques avances

Termine imperativement la section 4 avant de t'arreter."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return {**state, "roadmap": response.content[0].text, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur roadmap partie 1 : {str(e)}"}


def generer_roadmap_partie2(state: AuditState) -> AuditState:
    try:
        system = """Tu es un consultant senior en transformation IA.
Tu rediges des roadmaps professionnels en francais.
Tu termines TOUJOURS toutes tes sections avant de t'arreter."""

        prompt = f"""Redige les sections 5 a 8 du roadmap IA pour :

Entreprise : {state['entreprise']}
Secteur : {state['secteur']}
Budget IA : {state['budget_ia']}
Score global : {state['score_global']}/10

Contexte des phases deja definies :
{state['roadmap'][:1000]}

Redige ces 4 sections de facon detaillee et professionnelle :
5. BUDGET RECOMMANDE : tableau par phase avec totaux et couts recurrents
6. KPIS DE SUIVI : 3-4 KPIs mesurables par processus automatise
7. RISQUES ET MITIGATION : top 3 risques avec plan d action concret
8. PROCHAINES ETAPES IMMEDIATES : 3 actions concretes a lancer cette semaine

Termine IMPERATIVEMENT la section 8 avant de t'arreter."""

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8096,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        roadmap_complet = state["roadmap"] + "\n\n" + response.content[0].text
        return {**state, "roadmap": roadmap_complet, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur roadmap partie 2 : {str(e)}"}


def build_graph():
    graph = StateGraph(AuditState)
    graph.add_node("analyser_processus", analyser_processus)
    graph.add_node("identifier_opportunites", identifier_opportunites)
    graph.add_node("generer_roadmap_partie1", generer_roadmap_partie1)
    graph.add_node("generer_roadmap_partie2", generer_roadmap_partie2)

    graph.set_entry_point("analyser_processus")
    graph.add_edge("analyser_processus", "identifier_opportunites")
    graph.add_edge("identifier_opportunites", "generer_roadmap_partie1")
    graph.add_edge("generer_roadmap_partie1", "generer_roadmap_partie2")
    graph.add_edge("generer_roadmap_partie2", END)

    return graph.compile()