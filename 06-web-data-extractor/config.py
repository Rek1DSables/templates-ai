# ============================================================
# CONFIG — Agent extraction de données web
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "🌐 Extracteur de données web"
APP_SUBTITLE = "Extrayez et structurez automatiquement les données de n'importe quelle page web."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Formats d'extraction disponibles
EXTRACT_FORMATS = {
    "Liste structurée"  : "Extrais les informations clés sous forme de liste structurée avec titres et sous-points.",
    "Tableau JSON"      : "Extrais les données sous forme de JSON structuré avec des clés explicites.",
    "Résumé analytique" : "Analyse le contenu et produis un résumé analytique avec les points essentiels.",
}

# Langue de sortie
OUTPUT_LANGUE = "Français"

# Nombre maximum de caractères à analyser
MAX_CHARS = 12000