# ============================================================
# CREW — Agent de veille concurrentielle
# 3 agents : Scout, Analyst, Reporter
# ============================================================

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from config import MODEL, SEARCH_RESULTS, RAPPORT_SECTIONS, RAPPORT_LANGUE, RAPPORT_TON
import os

# ── Tools ──────────────────────────────────────────────────
def get_tools():
    return [SerperDevTool()]

# ── Crew factory ───────────────────────────────────────────
def build_crew(concurrents: list, secteur: str, client: str, length_instruction: str):
    tools = get_tools()
    sections = "\n".join([f"- {s}" for s in RAPPORT_SECTIONS])
    concurrents_str = ", ".join(concurrents)

    scout = Agent(
        role="Scout",
        goal=f"Rechercher les informations récentes sur : {concurrents_str}",
        backstory=f"Expert en veille concurrentielle dans le secteur : {secteur}.",
        tools=tools,
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    analyst = Agent(
        role="Analyst",
        goal=f"Analyser les informations collectées et identifier les tendances clés pour {client}.",
        backstory="Analyste stratégique senior spécialisé en intelligence compétitive.",
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    reporter = Agent(
        role="Reporter",
        goal=f"Produire un rapport de veille structuré, complet et concis en {RAPPORT_LANGUE}.",
        backstory=f"Rédacteur expert en rapports stratégiques. Ton : {RAPPORT_TON}.",
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    # ── Tasks ──────────────────────────────────────────────
    task_scout = Task(
        description=f"""
Recherche les informations récentes sur ces concurrents : {concurrents_str}.
Secteur : {secteur}.
Pour chaque concurrent, cherche : actualités, nouveaux produits, campagnes marketing, avis clients.
Limite : {SEARCH_RESULTS} résultats par concurrent.
""",
        expected_output="Données brutes structurées par concurrent.",
        agent=scout,
    )

    task_analyse = Task(
        description=f"""
À partir des données collectées par le Scout, analyse la situation concurrentielle.
Identifie les tendances, menaces et opportunités pour : {client}.
Secteur : {secteur}.
Sois concis : 2-3 points clés maximum par concurrent.
""",
        expected_output="Analyse stratégique concise avec tendances et opportunités.",
        agent=analyst,
    )

    task_report = Task(
        description=f"""
Rédige un rapport de veille concurrentielle en {RAPPORT_LANGUE}.
Ton : {RAPPORT_TON}.
Client : {client}
Concurrents analysés : {concurrents_str}

Règles STRICTES :
- {length_instruction}
- Le rapport doit être COMPLET, jamais coupé en milieu de phrase
- Termine toujours par une conclusion

Sections à couvrir :
{sections}

Retourne uniquement le rapport final, sans commentaires.
""",
        expected_output="Rapport complet, toutes sections couvertes, jamais tronqué.",
        agent=reporter,
    )

    crew = Crew(
        agents=[scout, analyst, reporter],
        tasks=[task_scout, task_analyse, task_report],
        process=Process.sequential,
        verbose=False,
    )

    return crew