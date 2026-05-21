import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Apify ────────────────────────────────────────────────────────────────────
APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")

# Acteurs Apify disponibles (ne pas modifier)
APIFY_GOOGLE_MAPS_ACTOR  = "Xb8osYTtOjlsgI6k9"
APIFY_TRUSTPILOT_ACTOR   = "misceres/trustpilot-scraper"

# ─── Paramètres scraping ──────────────────────────────────────────────────────
MAX_REVIEWS = 50   # nombre max de reviews à récupérer

# ─── Sources disponibles dans l'interface ─────────────────────────────────────
SOURCES = [
    "Google Maps",
    "Trustpilot",
]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5