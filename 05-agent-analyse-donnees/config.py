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

# Types d'analyse
TYPES_ANALYSE = [
    "Analyse exploratoire complète",
    "Détection d'anomalies",
    "Analyse de tendances",
    "Segmentation clients",
    "Analyse de performance commerciale",
    "Analyse financière",
]

# Formats export
FORMATS_EXPORT = ["PDF", "JSON", "CSV"]