import time
import requests
from typing import TypedDict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class SentimentState(TypedDict):
    # Input
    source:   str   # "Google Maps" ou "Trustpilot"
    url:      str   # URL de la page à analyser

    # Runtime
    raw_reviews:       Optional[list]
    reviews_text:      Optional[str]
    sentiment_analysis: Optional[str]
    themes:            Optional[str]
    report:            Optional[str]

    # Suivi
    errors: list
    status: str  # pending | scraped | analysed | completed | error

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

def _run_apify_actor(actor_id: str, run_input: dict) -> list:
    """Lance un acteur Apify et retourne les résultats."""
    # Lancement de l'acteur
    run_url = f"https://api.apify.com/v2/acts/{actor_id}/runs"
    response = requests.post(
        run_url,
        json=run_input,
        headers={"Content-Type": "application/json"},
        params={"token": config.APIFY_API_KEY, "waitForFinish": 120},
    )
    response.raise_for_status()
    run_data = response.json()
    dataset_id = run_data["data"]["defaultDatasetId"]

    # Récupération des résultats
    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items"
    results = requests.get(
        dataset_url,
        params={"token": config.APIFY_API_KEY, "limit": config.MAX_REVIEWS},
    )
    results.raise_for_status()
    return results.json()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def validate_input(state: SentimentState) -> SentimentState:
    errors = []
    if not state["url"].strip():
        errors.append("URL requise.")
    if "http" not in state["url"]:
        errors.append("URL invalide — doit commencer par http:// ou https://")
    if errors:
        return {**state, "errors": errors, "status": "error"}
    return {**state, "errors": [], "status": "pending"}


def scrape_reviews(state: SentimentState) -> SentimentState:
    """Récupère les reviews via Apify selon la source."""
    try:
        if state["source"] == "Google Maps":
            run_input = {
                "startUrls": [{"url": state["url"]}],
                "maxReviews": config.MAX_REVIEWS,
                "reviewsSort": "newest",
                "language": "fr",
            }
            actor_id = config.APIFY_GOOGLE_MAPS_ACTOR

        else:  # Trustpilot
            run_input = {
                "startUrls": [{"url": state["url"]}],
                "maxReviews": config.MAX_REVIEWS,
            }
            actor_id = config.APIFY_TRUSTPILOT_ACTOR

        raw_reviews = _run_apify_actor(actor_id, run_input)

        if not raw_reviews:
            return {**state, "errors": ["Aucune review récupérée. Vérifiez l'URL."], "status": "error"}

        return {**state, "raw_reviews": raw_reviews, "status": "scraped"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Scraping Apify : {e}"], "status": "error"}


def format_reviews(state: SentimentState) -> SentimentState:
    """Formate les reviews brutes en texte exploitable par le LLM."""
    try:
        reviews = state["raw_reviews"]
        lines = []

        for i, r in enumerate(reviews[:config.MAX_REVIEWS], 1):
            # Compatibilité Google Maps et Trustpilot
            author = r.get("reviewer", {}).get("name") or r.get("author", "Anonyme")
            rating = r.get("stars") or r.get("rating", "?")
            text   = r.get("text") or r.get("reviewBody") or r.get("body", "")

            if text:
                lines.append(f"[{i}] {author} — {rating}⭐\n{text.strip()}\n")

        reviews_text = "\n".join(lines)
        return {**state, "reviews_text": reviews_text}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Formatage reviews : {e}"], "status": "error"}


def analyse_sentiment(state: SentimentState) -> SentimentState:
    """Analyse le sentiment global et par review."""
    try:
        prompt = f"""Tu analyses le sentiment de ces avis clients.

AVIS :
{state['reviews_text']}

Fournis :
1. Un score global de satisfaction sur 10
2. Répartition : X% positifs, X% neutres, X% négatifs
3. Les 3 points forts les plus mentionnés
4. Les 3 points faibles les plus mentionnés
5. Quelques verbatims marquants (positifs et négatifs)

Réponds en français, de manière structurée et concise.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "sentiment_analysis": response.content, "status": "analysed"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Analyse sentiment : {e}"], "status": "error"}


def extract_themes(state: SentimentState) -> SentimentState:
    """Identifie les thèmes récurrents dans les reviews."""
    try:
        prompt = f"""À partir de ces avis clients, identifie les thèmes récurrents.

AVIS :
{state['reviews_text']}

Pour chaque thème :
- Nom du thème
- Fréquence (nombre de mentions estimées)
- Sentiment associé (positif / négatif / mixte)
- Citation représentative courte

Limite-toi aux 5 thèmes les plus importants.
Réponds en français, format structuré.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "themes": response.content}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Extraction thèmes : {e}"], "status": "error"}


def generate_report(state: SentimentState) -> SentimentState:
    """Génère le rapport de synthèse final."""
    try:
        prompt = f"""Tu rédiges un rapport de synthèse professionnel basé sur l'analyse suivante.

ANALYSE SENTIMENT :
{state['sentiment_analysis']}

THÈMES IDENTIFIÉS :
{state['themes']}

Le rapport doit inclure :
- Un résumé exécutif (3-4 phrases)
- Les points d'action prioritaires (3 recommandations concrètes)
- Une conclusion

Ton professionnel, français, destiné à un dirigeant d'entreprise.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        return {**state, "report": response.content, "status": "completed"}

    except Exception as e:
        return {**state, "errors": state["errors"] + [f"Génération rapport : {e}"], "status": "error"}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(SentimentState)

    g.add_node("validate_input",  validate_input)
    g.add_node("scrape_reviews",  scrape_reviews)
    g.add_node("format_reviews",  format_reviews)
    g.add_node("analyse_sentiment", analyse_sentiment)
    g.add_node("extract_themes",  extract_themes)
    g.add_node("generate_report", generate_report)

    g.set_entry_point("validate_input")

    g.add_conditional_edges("validate_input",    _stop_on_error("scrape_reviews"))
    g.add_conditional_edges("scrape_reviews",    _stop_on_error("format_reviews"))
    g.add_conditional_edges("format_reviews",    _stop_on_error("analyse_sentiment"))
    g.add_conditional_edges("analyse_sentiment", _stop_on_error("extract_themes"))
    g.add_conditional_edges("extract_themes",    _stop_on_error("generate_report"))
    g.add_edge("generate_report", END)

    return g.compile()


def run_analysis(source: str, url: str) -> SentimentState:
    initial_state = SentimentState(
        source             = source,
        url                = url,
        raw_reviews        = None,
        reviews_text       = None,
        sentiment_analysis = None,
        themes             = None,
        report             = None,
        errors             = [],
        status             = "pending",
    )
    return build_graph().invoke(initial_state)