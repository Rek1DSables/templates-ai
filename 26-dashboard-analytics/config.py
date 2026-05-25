import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ─── Dashboard ────────────────────────────────────────────────────────────────
COMPANY_NAME = "Votre Entreprise"

# ─── Périodes d'analyse ───────────────────────────────────────────────────────
PERIODS = ["7 derniers jours", "30 derniers jours", "90 derniers jours", "12 derniers mois"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5