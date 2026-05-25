import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "invoices"

# ─── Catégories comptables ────────────────────────────────────────────────────
EXPENSE_CATEGORIES = [
    "Fournitures de bureau",
    "Services informatiques",
    "Frais de déplacement",
    "Marketing & Communication",
    "Sous-traitance",
    "Loyer & Charges",
    "Utilities",
    "Matériel & Équipement",
    "Formation",
    "Autre",
]

# ─── TVA ──────────────────────────────────────────────────────────────────────
TVA_RATES = [0.0, 5.5, 10.0, 20.0]   # taux TVA France

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5