import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# ─── RAG ──────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE      = 500
CHUNK_OVERLAP   = 50
TOP_K           = 4   # chunks par source

# ─── Interface ────────────────────────────────────────────────────────────────
CHATBOT_NAME    = "Assistant Multi-Sources"
WELCOME_MESSAGE = "Bonjour ! Uploadez vos PDFs, connectez Supabase ou une API, puis posez vos questions."

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5