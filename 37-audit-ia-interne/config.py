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

# Audit
SECTEURS = [
    "Tech / SaaS",
    "E-commerce",
    "Finance / Comptabilite",
    "RH / Recrutement",
    "Marketing / Communication",
    "Juridique",
    "Sante",
    "Industrie / Logistique",
    "Conseil / Consulting",
    "Autre",
]

TAILLES = [
    "1-10 employes",
    "10-50 employes",
    "50-200 employes",
    "200-1000 employes",
    "1000+ employes",
]