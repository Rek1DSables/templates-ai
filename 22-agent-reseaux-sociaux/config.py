import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Serper ───────────────────────────────────────────────────────────────────
SERPER_API_KEY = os.getenv("SERPER_API_KEY", "")

# ─── Entreprise ───────────────────────────────────────────────────────────────
COMPANY_NAME    = "Votre Entreprise"
COMPANY_SECTOR  = "Votre secteur"
TARGET_AUDIENCE = "Votre audience cible"

# ─── Plateformes ──────────────────────────────────────────────────────────────
PLATFORMS = ["LinkedIn", "Twitter/X", "Instagram", "Facebook"]

# ─── Tonalités ────────────────────────────────────────────────────────────────
TONES = ["Professionnel", "Décontracté", "Inspirant", "Éducatif", "Humoristique"]

# ─── Planning ─────────────────────────────────────────────────────────────────
POSTS_PER_WEEK = 5   # nombre de posts générés par semaine

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5