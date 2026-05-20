# ============================================================
# CONFIG — Résumeur automatique de documents
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "📄 Résumeur de documents"
APP_SUBTITLE = "Uploadez vos PDFs et obtenez un résumé structuré en quelques secondes."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Taille des chunks (en caractères)
CHUNK_SIZE = 3000
CHUNK_OVERLAP = 200

# Options de sortie
OUTPUT_FORMATS = {
    "Résumé court"      : "Un paragraphe de 5 à 8 lignes maximum.",
    "Résumé structuré"  : "Points clés, conclusions et recommandations en bullet points.",
    "Fiche de synthèse" : "Titre, contexte, points clés, citations importantes, conclusion.",
}

# Langue de sortie
OUTPUT_LANGUE = "Français"