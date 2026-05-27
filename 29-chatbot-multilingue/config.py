# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "chatbot_conversations"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Langues supportees
LANGUES_SUPPORTEES = [
    "Français", "English", "Español", "Deutsch",
    "Italiano", "Português", "Nederlands", "Polski",
    "中文", "日本語", "العربية",
]

# Base de connaissance par defaut
BASE_CONNAISSANCE_DEFAUT = """
PRODUIT : Assistant IA Multilingue
ENTREPRISE : Acme Corp

FAQ :
Q: Comment fonctionne votre produit ?
R: Notre produit utilise l'intelligence artificielle pour automatiser vos processus metier.

Q: Quels sont vos tarifs ?
R: Nos tarifs commencent a 49 EUR/mois pour le plan Starter.

Q: Comment contacter le support ?
R: Vous pouvez nous contacter par email a support@acme.com ou par chat.

Q: Est-ce que vous proposez un essai gratuit ?
R: Oui, nous proposons 14 jours d'essai gratuit sans carte bancaire.

Q: Dans quelles langues est disponible votre produit ?
R: Notre produit est disponible en plus de 10 langues.

POLITIQUE : Les remboursements sont possibles dans les 30 jours suivant l'achat.
HORAIRES : Support disponible du lundi au vendredi, 9h-18h CET.
"""