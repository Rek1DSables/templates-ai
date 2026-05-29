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

# Orchestrateur
MAX_SOUS_TACHES = 4
MAX_RETRIES = 3
RETRY_DELAY = 5