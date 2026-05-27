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
SUPABASE_TABLE = "rapports"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Config
SECTEURS = ["Tech / SaaS", "E-commerce", "Finance", "Marketing", "RH", "Industrie", "Autre"]
PERIODES = ["Semaine", "Mois", "Trimestre", "Annee"]