# ============================================================
# CONFIG — Générateur de contenu marketing
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "✍️ Générateur de contenu marketing"
APP_SUBTITLE = "Produisez articles, posts LinkedIn et newsletters en quelques secondes."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Types de contenu disponibles
CONTENT_TYPES = [
    "Article de blog",
    "Post LinkedIn",
    "Newsletter",
    "Fiche produit",
    "Email commercial",
]

# Langues disponibles
LANGUAGES = ["Français", "Anglais", "Espagnol"]

# Tonalités disponibles
TONES = ["Professionnel", "Décontracté", "Inspirant", "Humoristique", "Technique"]

# Longueurs disponibles
LENGTHS = {
    "Court (150 mots)"  : 150,
    "Moyen (300 mots)"  : 300,
    "Long (600 mots)"   : 600,
}

# Clé API Serper pour la recherche web (optionnel)
USE_WEB_SEARCH = True