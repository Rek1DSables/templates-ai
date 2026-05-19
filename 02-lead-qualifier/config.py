# ============================================================
# CONFIG — Pipeline de qualification de leads
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "🎯 Pipeline de Qualification de Leads"
APP_SUBTITLE = "Analyse automatique de vos prospects par IA"

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Seuils de scoring
SCORE_CHAUD = 7   # >= 7 → chaud
SCORE_TIEDE = 4   # >= 4 → tiède, < 4 → froid

# Critères de scoring (affichés dans l'interface)
CRITERES = """
- Mentionne un budget : +3 points
- Mentionne une taille d'équipe : +2 points
- Besoin clair et précis : +3 points
- Ton professionnel : +2 points
"""

# Longueur max des emails générés
EMAIL_CHAUD_MOTS = 80
EMAIL_TIEDE_MOTS = 60

# Labels affichés
LABEL_CHAUD = "🔴 CHAUD"
LABEL_TIEDE = "🟡 TIÈDE"
LABEL_FROID = "🔵 FROID"