# ============================================================
# CREW — Générateur de contenu marketing
# 3 agents : Researcher, Writer, Editor
# ============================================================

from crewai import Agent, Task, Crew, Process
from crewai_tools import SerperDevTool
from config import MODEL, USE_WEB_SEARCH
import os

# ── Tools ──────────────────────────────────────────────────
def get_tools():
    if USE_WEB_SEARCH and os.getenv("SERPER_API_KEY"):
        return [SerperDevTool()]
    return []

# ── Crew factory ───────────────────────────────────────────
def build_crew(brief: str, content_type: str, tone: str, language: str, length: int):
    tools = get_tools()

    researcher = Agent(
        role="Researcher",
        goal=f"Trouver les informations clés et tendances sur le sujet : {brief}",
        backstory="Expert en recherche d'information et veille marketing.",
        tools=tools,
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    writer = Agent(
        role="Writer",
        goal=f"Rédiger un {content_type} de {length} mots sur : {brief}",
        backstory=f"Rédacteur expert en marketing digital. Ton : {tone}. Langue : {language}.",
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    editor = Agent(
        role="Editor",
        goal="Relire, corriger et améliorer le contenu produit par le Writer.",
        backstory="Éditeur senior spécialisé en contenu marketing. Exigeant sur la qualité.",
        llm=f"anthropic/{MODEL}",
        verbose=False,
    )

    # ── Tasks ──────────────────────────────────────────────
    task_research = Task(
        description=f"""
Recherche les informations clés, tendances et angles intéressants sur : {brief}.
Produis un résumé structuré des points essentiels à couvrir.
""",
        expected_output="Résumé structuré avec les points clés à couvrir.",
        agent=researcher,
    )

    task_write = Task(
        description=f"""
À partir du résumé du Researcher, rédige un {content_type} de {length} mots.
Ton : {tone}. Langue : {language}.
Sujet : {brief}
""",
        expected_output=f"{content_type} complet de {length} mots.",
        agent=writer,
    )

    task_edit = Task(
        description=f"""
Relis et améliore le {content_type} rédigé par le Writer.
Corrige les fautes, améliore le style, assure la cohérence du ton ({tone}).
Retourne la version finale uniquement, sans commentaires.
""",
        expected_output=f"Version finale du {content_type}, prête à publier.",
        agent=editor,
    )

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[task_research, task_write, task_edit],
        process=Process.sequential,
        verbose=False,
    )

    return crew