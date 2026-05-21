import os
import time

import config

os.environ["ANTHROPIC_API_KEY"] = config.ANTHROPIC_API_KEY

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool

# ─── Tools ───────────────────────────────────────────────────────────────────
search_tool = SerperDevTool(
    api_key=config.SERPER_API_KEY,
    n_results=config.MAX_SEARCH_RESULTS,
)

# ─── Agents ──────────────────────────────────────────────────────────────────
def create_agents():
    searcher = Agent(
        role="Recherchiste Senior",
        goal="Collecter des informations récentes et fiables sur le sujet demandé",
        backstory="""Tu es un expert en recherche d'informations. Tu sais identifier
        les sources les plus pertinentes et extraire les données clés sur n'importe
        quel secteur ou entreprise.""",
        tools=[search_tool],
        llm=f"anthropic/{config.MODEL_NAME}",
        verbose=True,
        max_iter=5,
    )

    analyst = Agent(
        role="Analyste de Marché",
        goal="Analyser les données collectées et identifier les tendances et opportunités clés",
        backstory="""Tu es un analyste de marché expérimenté. Tu transformes des données
        brutes en insights actionnables. Tu identifies les tendances, les acteurs clés,
        les opportunités et les menaces d'un marché.""",
        llm=f"anthropic/{config.MODEL_NAME}",
        verbose=True,
        max_iter=5,
    )

    writer = Agent(
        role="Rédacteur de Rapports",
        goal="Rédiger un rapport professionnel clair et structuré",
        backstory="""Tu es un rédacteur spécialisé dans les rapports d'analyse de marché.
        Tu transformes des analyses complexes en documents clairs, professionnels et
        accessibles pour des dirigeants d'entreprise.""",
        llm=f"anthropic/{config.MODEL_NAME}",
        verbose=True,
        max_iter=5,
    )

    critic = Agent(
        role="Réviseur Critique",
        goal="Vérifier la qualité, la cohérence et la complétude du rapport",
        backstory="""Tu es un réviseur exigeant. Tu vérifies que le rapport est complet,
        cohérent, bien structuré et répond parfaitement à la demande initiale.
        Tu proposes des améliorations concrètes si nécessaire.""",
        llm=f"anthropic/{config.MODEL_NAME}",
        verbose=True,
        max_iter=3,
    )

    return searcher, analyst, writer, critic


# ─── Tasks ───────────────────────────────────────────────────────────────────
def create_tasks(topic: str, searcher, analyst, writer, critic):
    search_task = Task(
        description=f"""Effectue des recherches approfondies sur : {topic}

        Collecte des informations sur :
        1. Vue d'ensemble du secteur / de l'entreprise
        2. Acteurs principaux et parts de marché
        3. Tendances récentes et innovations
        4. Données chiffrées (taille du marché, croissance, etc.)
        5. Actualités récentes (6 derniers mois)

        Utilise l'outil de recherche plusieurs fois avec des requêtes variées.
        Cite tes sources pour chaque information clé.""",
        agent=searcher,
        expected_output="Un document structuré avec toutes les informations collectées et leurs sources.",
    )

    analysis_task = Task(
        description=f"""Analyse les informations collectées sur : {topic}

        Sur la base des recherches effectuées, produis une analyse approfondie :
        1. Synthèse des données clés
        2. Tendances de fond identifiées
        3. Opportunités de marché
        4. Menaces et risques
        5. Analyse concurrentielle
        6. Perspectives à court et moyen terme

        Appuie-toi sur les données chiffrées collectées.""",
        agent=analyst,
        expected_output="Une analyse de marché complète et structurée avec insights actionnables.",
        context=[search_task],
    )

    writing_task = Task(
        description=f"""Rédige un rapport de marché professionnel sur : {topic}

        Le rapport doit inclure :
        1. Résumé exécutif (1 page max)
        2. Introduction et contexte
        3. Vue d'ensemble du marché
        4. Acteurs clés et positionnement
        5. Tendances et innovations
        6. Opportunités et menaces
        7. Recommandations stratégiques
        8. Conclusion

        Langue : français. Ton : professionnel et accessible.
        Format : sections claires avec titres et sous-titres.""",
        agent=writer,
        expected_output="Un rapport de marché complet, professionnel et bien structuré en français.",
        context=[search_task, analysis_task],
    )

    critic_task = Task(
        description=f"""Révise et améliore le rapport sur : {topic}

        Vérifie :
        1. Complétude — toutes les sections sont présentes et développées
        2. Cohérence — les informations sont cohérentes entre elles
        3. Clarté — le texte est clair et accessible
        4. Pertinence — le rapport répond bien à la demande initiale
        5. Qualité — niveau professionnel atteint

        Produis la version finale améliorée du rapport.
        Ne te contente pas de commenter — réécris les parties à améliorer.""",
        agent=critic,
        expected_output="La version finale et améliorée du rapport, prête à être livrée au client.",
        context=[writing_task],
    )

    return search_task, analysis_task, writing_task, critic_task


# ─── Run ─────────────────────────────────────────────────────────────────────
def run_research(topic: str) -> dict:
    """Lance le pipeline multi-agents et retourne le rapport final."""
    try:
        searcher, analyst, writer, critic = create_agents()
        search_task, analysis_task, writing_task, critic_task = create_tasks(
            topic, searcher, analyst, writer, critic
        )

        crew = Crew(
            agents  = [searcher, analyst, writer, critic],
            tasks   = [search_task, analysis_task, writing_task, critic_task],
            process = Process.sequential,
            verbose = True,
        )

        result = crew.kickoff()
        return {
            "status": "completed",
            "report": str(result),
            "errors": [],
        }

    except Exception as e:
        return {
            "status": "error",
            "report": "",
            "errors": [f"Pipeline CrewAI : {e}"],
        }