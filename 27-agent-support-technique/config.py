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
TECHNOLOGIES = [
    "Python",
    "JavaScript / Node.js",
    "React / Vue / Angular",
    "Docker / Kubernetes",
    "AWS / GCP / Azure",
    "PostgreSQL / MySQL",
    "API REST / GraphQL",
    "LangChain / LangGraph",
    "FastAPI / Django / Flask",
    "Autre",
]

NIVEAUX_URGENCE = ["Critique (production down)", "Haute (impact utilisateurs)", "Normale (bug non bloquant)", "Basse (amelioration)"]

TYPES_PROBLEME = [
    "Erreur / Exception",
    "Performance / Lenteur",
    "Bug logique",
    "Probleme de configuration",
    "Probleme de deploiement",
    "Securite / Vulnerability",
    "Autre",
]