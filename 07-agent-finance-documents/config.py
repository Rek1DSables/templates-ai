# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "documents_financiers"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Types de documents
TYPES_DOCUMENT = [
    "Facture",
    "Devis",
    "Avoir",
    "Bon de commande",
    "Relevé de compte",
    "Note de frais",
    "Bulletin de salaire",
]

# Modes
MODES = ["Analyser un document", "Générer un devis", "Générer une facture"]

# TVA
TAUX_TVA = [0.0, 5.5, 10.0, 20.0]