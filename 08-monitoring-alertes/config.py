import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL   = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY   = os.getenv("SUPABASE_KEY", "")
SUPABASE_TABLE = "monitoring_alerts"

# ─── Gmail (alertes email) ────────────────────────────────────────────────────
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE       = "token.json"
GMAIL_SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
ALERT_EMAIL            = os.getenv("ALERT_EMAIL", "")
SENDER_EMAIL           = os.getenv("SENDER_EMAIL", "")

# ─── Seuils d'alerte par défaut (personnalisables par client) ─────────────────
DEFAULT_THRESHOLDS = {
    "cpu_usage":      80.0,   # % CPU
    "memory_usage":   85.0,   # % RAM
    "disk_usage":     90.0,   # % disque
    "response_time":  2000.0, # ms
    "error_rate":     5.0,    # % erreurs
}

# ─── Niveaux d'alerte ─────────────────────────────────────────────────────────
ALERT_LEVELS = {
    "critical": 1.2,   # > 120% du seuil → critique
    "warning":  1.0,   # > 100% du seuil → avertissement
    "ok":       0.0,   # sous le seuil → OK
}

# ─── Métriques disponibles ────────────────────────────────────────────────────
METRICS = ["cpu_usage", "memory_usage", "disk_usage", "response_time", "error_rate"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5