import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "quiz_sessions"

# ─── Quiz ─────────────────────────────────────────────────────────────────────
QUESTIONS_PER_SESSION = 5     # questions par session
PASS_THRESHOLD        = 0.7   # score minimum pour passer au niveau suivant (70%)

# ─── Niveaux ──────────────────────────────────────────────────────────────────
LEVELS = ["Débutant", "Intermédiaire", "Avancé", "Expert"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5