# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Modes d'extraction
MODES_EXTRACTION = [
    "Extraire depuis une URL",
    "Extraire depuis une liste d'URLs",
    "Extraire depuis du texte brut",
]

# Types de données cibles
TYPES_EXTRACTION = [
    "Contacts (nom, email, téléphone, entreprise)",
    "Produits (nom, prix, description, disponibilité)",
    "Offres d'emploi (titre, entreprise, lieu, salaire)",
    "Actualités (titre, date, résumé, source)",
    "Avis clients (note, auteur, date, commentaire)",
    "Données personnalisées (champs libres)",
]

# Format de sortie
FORMATS_SORTIE = ["JSON", "CSV", "Tableau Streamlit"]

# Headers HTTP
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

# Timeout scraping
SCRAPING_TIMEOUT = 15