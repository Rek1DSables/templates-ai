# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Categories
CATEGORIES = [
    "Support client",
    "Demande commerciale",
    "Réclamation",
    "Partenariat",
    "Candidature",
    "Spam",
    "Autre",
]

# Priorites
PRIORITES = {
    "urgente": "🔴",
    "haute": "🟠",
    "normale": "🟡",
    "basse": "🟢",
}

# Nombre d'emails a traiter
NB_EMAILS_MAX = 10