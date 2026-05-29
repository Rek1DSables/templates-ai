# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Objectifs email
OBJECTIFS = [
    "Prospection commerciale",
    "Relance prospect froid",
    "Upsell client existant",
    "Invitation événement",
    "Annonce produit / feature",
    "Reengagement client inactif",
    "Suivi post-démo",
    "Demande de témoignage / avis",
]

# Tons
TONS = [
    "Professionnel et direct",
    "Chaleureux et personnalisé",
    "Urgent et impactant",
    "Educatif et informatif",
    "Storytelling",
]

# Delai entre envois (secondes)
DELAI_ENTRE_ENVOIS = 2