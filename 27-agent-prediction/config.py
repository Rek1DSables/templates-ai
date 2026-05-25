import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Prédiction ───────────────────────────────────────────────────────────────
FORECAST_PERIODS  = 30    # nombre de périodes à prédire
CONFIDENCE_LEVEL  = 0.95  # intervalle de confiance

# ─── Modèles disponibles ──────────────────────────────────────────────────────
MODELS = [
    "Moyenne mobile",
    "Régression linéaire",
    "Lissage exponentiel",
]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5