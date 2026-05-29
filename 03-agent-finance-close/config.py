# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Types de cloture
TYPES_CLOTURE = [
    "Clôture mensuelle",
    "Clôture trimestrielle",
    "Clôture annuelle",
    "Clôture de consolidation multi-entités",
]

# Agents disponibles
AGENTS_FINANCE = [
    "Agent Réconciliation",
    "Agent Variance & Écarts",
    "Agent Journal Entries",
    "Agent Disclosure & Reporting",
]

# Devises
DEVISES = ["EUR", "USD", "GBP", "CHF", "JPY"]

# Seuils d'alerte par defaut
SEUIL_ECART_CRITIQUE = 5.0  # % d'écart considéré critique
SEUIL_ECART_ELEVE = 2.0     # % d'écart considéré élevé

# Normes comptables
NORMES = ["IFRS", "French GAAP (PCG)", "US GAAP", "Autre"]