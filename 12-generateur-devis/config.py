import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "quotes"

# ─── Entreprise (à personnaliser par client) ──────────────────────────────────
COMPANY_NAME    = "Votre Entreprise"
COMPANY_ADDRESS = "12 rue de la Paix, 75001 Paris"
COMPANY_SIRET   = "123 456 789 00012"
COMPANY_EMAIL   = os.getenv("SENDER_EMAIL", "")
COMPANY_PHONE   = "+33 1 23 45 67 89"

# ─── TVA ──────────────────────────────────────────────────────────────────────
TVA_RATE        = 20.0   # % TVA par défaut
PAYMENT_TERMS   = 30     # jours de délai de paiement

# ─── Devise ───────────────────────────────────────────────────────────────────
CURRENCY        = "EUR"
CURRENCY_SYMBOL = "EUR"

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5