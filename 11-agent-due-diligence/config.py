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

# Types de due diligence
TYPES_DD = [
    "Due Diligence M&A (Acquisition)",
    "Due Diligence Investissement (VC/PE)",
    "Due Diligence Partenariat Stratégique",
    "Due Diligence Fournisseur",
    "Due Diligence Immobilier Commercial",
]

# Axes d'analyse
AXES_ANALYSE = [
    "Financier",
    "Juridique et contractuel",
    "Commercial et marché",
    "Opérationnel",
    "Technologique",
    "RH et management",
    "Risques et conformité",
]

# Niveaux de risque
NIVEAUX_RISQUE = {
    "critique": "🔴",
    "eleve": "🟠",
    "moyen": "🟡",
    "faible": "🟢",
}