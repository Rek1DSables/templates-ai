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

# Config
TYPES_CONTRAT = [
    "Contrat de prestation de services",
    "Contrat de travail",
    "Contrat de vente",
    "NDA / Accord de confidentialite",
    "CGV / CGU",
    "Contrat de partenariat",
    "Bail commercial",
    "Contrat de licence",
    "Autre",
]

NIVEAUX_RISQUE = {
    "critique": "🔴",
    "eleve": "🟠",
    "moyen": "🟡",
    "faible": "🟢",
}