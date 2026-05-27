import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── RAG ──────────────────────────────────────────────────────────────────────
EMBEDDING_MODEL   = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE        = 500    # taille des chunks en caractères
CHUNK_OVERLAP     = 50     # chevauchement entre chunks
TOP_K             = 3      # nombre de chunks retournés par la recherche

# ─── Interface ────────────────────────────────────────────────────────────────
COMPANY_NAME      = "Votre Entreprise"
CHATBOT_NAME      = "Assistant Documentation"
WELCOME_MESSAGE   = "Bonjour ! Je suis votre assistant. Posez-moi vos questions sur la documentation."

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5