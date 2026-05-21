import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Apify ────────────────────────────────────────────────────────────────────
APIFY_API_KEY = os.getenv("APIFY_API_KEY", "")

# Acteur Apify pour LinkedIn
APIFY_LINKEDIN_ACTOR = "LpVuK3Zozwuipa5bp" # LinkedIn Profile Scraper

# ─── Paramètres prospection ───────────────────────────────────────────────────
MAX_PROFILES = 20   # nombre max de profils à traiter

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5