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
SUPABASE_TABLE = "rapports_clients"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Config
TYPES_MISSION = [
    "Developpement web / app",
    "AI / Automatisation",
    "Marketing digital",
    "SEO / Contenu",
    "Conseil / Strategie",
    "Design / UX",
    "Data / Analytics",
    "Autre",
]

PERIODES = ["Mensuel", "Bimensuel", "Trimestriel", "Fin de mission"]