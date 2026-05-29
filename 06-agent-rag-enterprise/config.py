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

# RAG Config
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100
TOP_K = 5
SIMILARITY_THRESHOLD = 0.3

# Embedding model (HuggingFace local, gratuit)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Types de documents supportés
TYPES_DOCUMENTS = [
    "Contrats et accords",
    "Documentation technique",
    "Politiques et procédures internes",
    "Rapports financiers",
    "Base de connaissances support",
    "Cahiers des charges",
    "Autre",
]

# Niveaux de permissions
NIVEAUX_PERMISSION = {
    "public": "🟢 Public — accessible à tous",
    "interne": "🟡 Interne — collaborateurs uniquement",
    "confidentiel": "🟠 Confidentiel — direction et managers",
    "secret": "🔴 Secret — accès restreint nominatif",
}

# Profils utilisateurs
PROFILS_UTILISATEUR = [
    "Employé standard",
    "Manager",
    "Directeur",
    "Administrateur",
    "Support client",
    "Commercial",
    "Juridique",
]

# Seuils qualité RAG
SEUIL_CONFIANCE_ELEVE = 0.7
SEUIL_CONFIANCE_MOYEN = 0.4