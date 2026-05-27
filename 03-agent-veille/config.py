# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Serper
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "veille"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Veille
TYPES_VEILLE = [
    "Concurrentielle",
    "Sectorielle",
    "Reglementaire",
    "Technologique",
    "Multi-sources",
]
NIVEAUX_ALERTE = ["critique", "important", "informatif"]