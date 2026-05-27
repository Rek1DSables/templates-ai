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
SUPABASE_TABLE = "propales"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Config
TYPES_MISSION = [
    "Developpement AI / Agents",
    "Automatisation de processus",
    "Integration API / SaaS",
    "Conseil en transformation digitale",
    "Developpement web / mobile",
    "Data / Analytics",
    "Autre",
]

MODES_FACTURATION = [
    "Forfait",
    "Regie (jour/homme)",
    "Abonnement mensuel",
    "Success fee",
]