import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "onboarding_clients"

# ─── Gmail OAuth2 ─────────────────────────────────────────────────────────────
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE       = "token.json"
GMAIL_SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
SENDER_EMAIL           = os.getenv("SENDER_EMAIL", "")

# ─── Identité entreprise (à personnaliser par client) ─────────────────────────
COMPANY_NAME = "Votre Entreprise"
COMPANY_SIGNATURE = f"""

---
Cordialement,
L'équipe {COMPANY_NAME}

Cet email a été envoyé automatiquement. Merci de ne pas y répondre directement.
"""

# ─── Secteurs ─────────────────────────────────────────────────────────────────
SECTORS = [
    "E-commerce",
    "Finance & Comptabilité",
    "Santé & Bien-être",
    "RH & Recrutement",
    "Immobilier",
    "Juridique",
    "Marketing & Communication",
    "Logistique & Supply Chain",
    "SaaS & Technologie",
    "Autre",
]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5