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

# Serper
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Canaux
CANAUX_CONTENU = [
    "Article de blog",
    "Post LinkedIn",
    "Thread Twitter/X",
    "Newsletter",
    "Email marketing",
    "Script vidéo YouTube",
    "Carrousel Instagram",
]

# Tons
TONS = [
    "Professionnel",
    "Educatif",
    "Inspirant",
    "Humoristique",
    "Direct et percutant",
    "Storytelling",
]

# Longueurs
LONGUEURS = {
    "Court (< 300 mots)": 300,
    "Moyen (300-600 mots)": 600,
    "Long (600-1200 mots)": 1200,
    "Très long (1200+ mots)": 2000,
}