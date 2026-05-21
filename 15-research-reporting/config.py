import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Serper (Google Search) ───────────────────────────────────────────────────
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ─── Rapport ──────────────────────────────────────────────────────────────────
COMPANY_NAME  = "Votre Entreprise"
REPORT_TITLE  = "Rapport de Recherche & Analyse"

# ─── Agents ───────────────────────────────────────────────────────────────────
MAX_SEARCH_RESULTS = 5   # résultats par recherche Serper

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5