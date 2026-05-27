import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Serper ───────────────────────────────────────────────────────────────────
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "legal_watches"

# ─── Domaines juridiques disponibles ─────────────────────────────────────────
LEGAL_DOMAINS = [
    "RGPD & Protection des données",
    "Droit du travail",
    "Droit des sociétés",
    "Fiscalité & TVA",
    "Droit de la consommation",
    "Propriété intellectuelle",
    "Cybersécurité & NIS2",
    "IA & Réglementation (AI Act)",
    "Droit commercial",
]

# ─── Pays / Juridictions ──────────────────────────────────────────────────────
JURISDICTIONS = ["France", "Union Européenne", "France + UE"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5