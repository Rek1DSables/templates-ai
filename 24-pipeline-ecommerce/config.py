import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL         = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY         = os.getenv("SUPABASE_KEY", "")
ORDERS_TABLE         = "orders"
PRODUCTS_TABLE       = "products"
ALERTS_TABLE         = "ecommerce_alerts"

# ─── Gmail ────────────────────────────────────────────────────────────────────
GMAIL_CREDENTIALS_FILE = "credentials.json"
GMAIL_TOKEN_FILE       = "token.json"
GMAIL_SCOPES           = ["https://www.googleapis.com/auth/gmail.send"]
SENDER_EMAIL           = os.getenv("SENDER_EMAIL", "")
ALERT_EMAIL            = os.getenv("ALERT_EMAIL", "")

# ─── Seuils ───────────────────────────────────────────────────────────────────
LOW_STOCK_THRESHOLD  = 10    # alerte si stock < 10 unités
HIGH_VALUE_ORDER     = 500   # alerte si commande > 500€

# ─── Statuts commandes ────────────────────────────────────────────────────────
ORDER_STATUSES = ["En attente", "Confirmée", "En préparation", "Expédiée", "Livrée", "Annulée"]

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5