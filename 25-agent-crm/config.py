import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL      = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY      = os.getenv("SUPABASE_KEY", "")
CONTACTS_TABLE    = "crm_contacts"
INTERACTIONS_TABLE = "crm_interactions"
OPPORTUNITIES_TABLE = "crm_opportunities"

# ─── Pipeline de vente ────────────────────────────────────────────────────────
PIPELINE_STAGES = [
    "Prospect",
    "Qualifié",
    "Proposition envoyée",
    "Négociation",
    "Gagné",
    "Perdu",
]

# ─── Scoring ──────────────────────────────────────────────────────────────────
INTERACTION_TYPES = ["Email", "Appel", "Réunion", "LinkedIn", "Démonstration", "Autre"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5