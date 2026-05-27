# graph.py
import time
import requests
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    SERPER_API_KEY, SERPER_URL,
    MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContentState(TypedDict):
    sujet: str
    secteur: str
    ton: str
    cible: str
    contexte_recherche: str
    article_blog: str
    post_linkedin: str
    post_twitter: str
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


def rechercher_contexte(state: ContentState) -> ContentState:
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": f"{state['sujet']} {state['secteur']} 2025", "num": 5}
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        data = response.json()

        resultats = []
        for item in data.get("organic", [])[:5]:
            titre = item.get("title", "")
            snippet = item.get("snippet", "")
            resultats.append(f"- {titre} : {snippet}")

        contexte = "\n".join(resultats) if resultats else "Aucun resultat."
        return {**state, "contexte_recherche": contexte, "erreur": ""}
    except Exception as e:
        return {**state, "contexte_recherche": "", "erreur": f"Erreur recherche : {str(e)}"}


def rediger_article_blog(state: ContentState) -> ContentState:
    try:
        system = f"""Tu es un redacteur content marketing expert.
Tu rediges des articles de blog professionnels, engageants et optimises SEO.
Ton : {state['ton']}
Cible : {state['cible']}
Tu reponds toujours en francais."""

        prompt = f"""Redige un article de blog complet sur : {state['sujet']}

Secteur : {state['secteur']}
Contexte et tendances actuelles :
{state['contexte_recherche']}

Structure :
- Titre accrocheur (H1)
- Introduction engageante (2-3 paragraphes)
- 3-4 sections avec sous-titres (H2)
- Exemples concrets et chiffres si disponibles
- Conclusion avec call-to-action
- Longueur : 600-800 mots"""

        article = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return {**state, "article_blog": article, "erreur": ""}
    except Exception as e:
        return {**state, "article_blog": "", "erreur": f"Erreur article : {str(e)}"}


def rediger_post_linkedin(state: ContentState) -> ContentState:
    try:
        system = f"""Tu es un expert en personal branding LinkedIn.
Tu rediges des posts LinkedIn viraux qui generent de l'engagement.
Ton : {state['ton']}
Cible : {state['cible']}
Tu reponds toujours en francais."""

        prompt = f"""Redige un post LinkedIn percutant sur : {state['sujet']}

Secteur : {state['secteur']}
Contexte :
{state['contexte_recherche']}

Regles LinkedIn :
- Accroche forte sur la premiere ligne (stoppe le scroll)
- Espaces entre les paragraphes pour la lisibilite
- 3-5 emojis strategiquement places
- Storytelling ou donnee choc en ouverture
- 3-5 points cles
- Question ou CTA en conclusion
- 5-8 hashtags pertinents en fin de post
- Longueur : 150-250 mots"""

        post = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
        )
        return {**state, "post_linkedin": post, "erreur": ""}
    except Exception as e:
        return {**state, "post_linkedin": "", "erreur": f"Erreur LinkedIn : {str(e)}"}


def rediger_post_twitter(state: ContentState) -> ContentState:
    try:
        system = f"""Tu es un expert en communication Twitter/X.
Tu rediges des threads et posts Twitter percutants et viraux.
Ton : {state['ton']}
Cible : {state['cible']}
Tu reponds toujours en francais."""

        prompt = f"""Redige un thread Twitter/X sur : {state['sujet']}

Secteur : {state['secteur']}
Contexte :
{state['contexte_recherche']}

Format thread (5-7 tweets) :
- Tweet 1 : accroche choc qui donne envie de lire la suite
- Tweets 2-5 : points cles, un par tweet, avec chiffres ou exemples
- Tweet 6 : conclusion actionnable
- Tweet 7 : CTA + question pour engagement
- Chaque tweet < 280 caracteres
- Numerote : 1/ 2/ 3/ etc.
- 2-3 emojis par tweet maximum"""

        thread = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return {**state, "post_twitter": thread, "erreur": ""}
    except Exception as e:
        return {**state, "post_twitter": "", "erreur": f"Erreur Twitter : {str(e)}"}


def build_graph():
    graph = StateGraph(ContentState)
    graph.add_node("rechercher_contexte", rechercher_contexte)
    graph.add_node("rediger_article_blog", rediger_article_blog)
    graph.add_node("rediger_post_linkedin", rediger_post_linkedin)
    graph.add_node("rediger_post_twitter", rediger_post_twitter)

    graph.set_entry_point("rechercher_contexte")
    graph.add_edge("rechercher_contexte", "rediger_article_blog")
    graph.add_edge("rediger_article_blog", "rediger_post_linkedin")
    graph.add_edge("rediger_post_linkedin", "rediger_post_twitter")
    graph.add_edge("rediger_post_twitter", END)

    return graph.compile()