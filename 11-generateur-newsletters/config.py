import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Gmail ────────────────────────────────────────────────────────────────────
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE       = "token.json"
GMAIL_SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
SENDER_EMAIL           = os.getenv("SENDER_EMAIL", "")

# ─── Newsletter ───────────────────────────────────────────────────────────────
COMPANY_NAME    = "Votre Entreprise"
UNSUBSCRIBE_URL = "https://votre-site.com/unsubscribe"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "newsletter_subscribers"

# ─── Tonalités disponibles ────────────────────────────────────────────────────
TONES = ["Professionnel", "Décontracté", "Inspirant", "Éducatif", "Promotionnel"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5