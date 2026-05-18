# ============================================================
# CONFIG — Chatbot FAQ intelligent
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "💬 Chatbot FAQ"
APP_SUBTITLE = "Posez vos questions, je réponds en me basant sur vos documents."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Dossier contenant les PDFs de la base de connaissance
DOCS_FOLDER = "docs"

# Nombre de chunks retournés par la recherche vectorielle
TOP_K = 4

# Taille des chunks (en caractères)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# Message affiché quand aucune réponse trouvée
NO_ANSWER_MSG = "Je n'ai pas trouvé de réponse dans les documents fournis."

# Modèle d'embeddings
EMBEDDING_MODEL = "BAAI/bge-m3"