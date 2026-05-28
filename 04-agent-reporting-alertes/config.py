# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "rapports"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Secteurs
SECTEURS = [
    "E-commerce",
    "SaaS B2B",
    "Retail",
    "Finance",
    "Santé",
    "Industrie",
    "Services",
    "Autre",
]

# Periodes
PERIODES = ["Journalier", "Hebdomadaire", "Mensuel", "Trimestriel"]

# Seuils d'alerte par defaut
SEUILS_DEFAUT = {
    "taux_conversion": {"min": 2.0, "max": 100.0, "unite": "%"},
    "churn": {"min": 0.0, "max": 5.0, "unite": "%"},
    "nps": {"min": 30.0, "max": 100.0, "unite": ""},
    "mrr": {"min": 0.0, "max": 999999.0, "unite": "EUR"},
}