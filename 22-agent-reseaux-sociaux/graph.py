import time
import json
from typing import TypedDict, Optional
from datetime import datetime, timedelta

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
import requests

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class SocialMediaState(TypedDict):
    # Input
    topic:     str
    platforms: list
    tone:      str
    objective: str   # notoriété | engagement | conversion | éducation

    # Runtime
    trending_topics: Optional[list]
    posts:           Optional[list]   # [{platform, content, hashtags, best_time}]
    planning:        Optional[list]   # planning hebdomadaire

    # Suivi
    errors: list
    status: str

# ─── Helpers ─────────────────────────────────────────────────────────────────
def invoke_with_retry(chain, input_data):
    for attempt in range(config.MAX_RETRIES):
        try:
            return chain.invoke(input_data)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < config.MAX_RETRIES - 1:
                time.sleep(config.RETRY_DELAY)
                continue
            raise

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

def _search_trending(topic: str) -> list:
    """Recherche les tendances via Serper."""
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": config.SERPER_API_KEY, "Content-Type": "application/json"},
            json={"q": f"{topic} tendances 2026", "gl": "fr", "hl": "fr", "num": 5},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json().get("organic", [])
        return [r.get("title", "") for r in results[:5]]
    except:
        return []

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def research_trends(state: SocialMediaState) -> SocialMediaState:
    """Recherche les tendances actuelles sur le sujet."""
    try:
        trending = _search_trending(state["topic"])
        return {**state, "trending_topics": trending}
    except Exception as e:
        return {**state, "trending_topics": [], "errors": state["errors"] + [f"Recherche tendances : {e}"]}


def generate_posts(state: SocialMediaState) -> SocialMediaState:
    """Génère des posts adaptés à chaque plateforme."""
    try:
        trending_text = "\n".join(state["trending_topics"]) if state["trending_topics"] else "Aucune tendance trouvée"

        posts = []
        for platform in state["platforms"]:
            prompt = f"""Tu es un expert en marketing digital. Génère un post {platform} percutant.

Entreprise : {config.COMPANY_NAME}
Secteur : {config.COMPANY_SECTOR}
Audience : {config.TARGET_AUDIENCE}
Sujet : {state['topic']}
Objectif : {state['objective']}
Tonalité : {state['tone']}
Tendances actuelles : {trending_text}

Contraintes par plateforme :
- LinkedIn : 1200 caractères max, ton professionnel, storytelling
- Twitter/X : 280 caractères max, percutant, accrocheur
- Instagram : 2200 caractères max, émotionnel, visuel
- Facebook : 500 caractères max, conversationnel

Réponds UNIQUEMENT avec un JSON valide :
{{
    "platform": "{platform}",
    "content": "texte du post",
    "hashtags": ["hashtag1", "hashtag2", "hashtag3"],
    "best_time": "meilleur moment pour publier (ex: Mardi 10h)",
    "tip": "conseil pour maximiser la portée"
}}
"""
            response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
            content  = response.content.strip().replace("```json", "").replace("```", "").strip()
            post     = json.loads(content)
            posts.append(post)

        return {**state, "posts": posts, "status": "posts_generated"}

    except Exception as e:
        return {**state, "errors": [f"Génération posts : {e}"], "status": "error"}


def generate_planning(state: SocialMediaState) -> SocialMediaState:
    """Génère un planning de publication hebdomadaire."""
    try:
        posts_summary = "\n".join([
            f"- {p['platform']} : {p['content'][:80]}... | Meilleur moment : {p['best_time']}"
            for p in state["posts"]
        ])

        prompt = f"""Tu es un social media manager. Génère un planning de publication hebdomadaire.

Posts disponibles :
{posts_summary}

Objectif : {state['objective']}
Nombre de posts par semaine : {config.POSTS_PER_WEEK}

Génère un planning sur 7 jours en tenant compte des meilleurs moments de publication.

Réponds UNIQUEMENT avec un JSON valide :
[
  {{
    "day": "Lundi",
    "date": "J+1",
    "platform": "LinkedIn",
    "time": "10h00",
    "content_preview": "début du post...",
    "objective": "notoriété"
  }}
]
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        content  = response.content.strip().replace("```json", "").replace("```", "").strip()
        planning = json.loads(content)

        return {**state, "planning": planning, "status": "completed"}

    except Exception as e:
        return {**state, "errors": [f"Génération planning : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(SocialMediaState)

    g.add_node("research_trends",  research_trends)
    g.add_node("generate_posts",   generate_posts)
    g.add_node("generate_planning", generate_planning)

    g.set_entry_point("research_trends")

    g.add_edge("research_trends", "generate_posts")
    g.add_conditional_edges("generate_posts",   _stop_on_error("generate_planning"))
    g.add_edge("generate_planning", END)

    return g.compile()


def run_social_media(topic: str, platforms: list, tone: str, objective: str) -> SocialMediaState:
    initial_state = SocialMediaState(
        topic           = topic,
        platforms       = platforms,
        tone            = tone,
        objective       = objective,
        trending_topics = None,
        posts           = None,
        planning        = None,
        errors          = [],
        status          = "pending",
    )
    return build_graph().invoke(initial_state)