import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Rapport ──────────────────────────────────────────────────────────────────
COMPANY_NAME   = "Votre Entreprise"
REPORT_TITLE   = "Rapport d'Analyse Automatique"
REPORT_AUTHOR  = "Pipeline IA"

# ─── Paramètres analyse ───────────────────────────────────────────────────────
MAX_ROWS_PREVIEW = 50   # nombre de lignes envoyées au LLM pour analyse

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5