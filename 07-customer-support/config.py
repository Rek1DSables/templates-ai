# ============================================================
# CONFIG — Agent support client multi-canal
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "🎧 Agent Support Client"
APP_SUBTITLE = "Triaging automatique, réponse draft et escalade intelligente."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Seuils de confiance
SCORE_AUTO_REPONSE = 7   # >= 7 → réponse automatique
SCORE_ESCALADE     = 4   # < 4  → escalade humaine

# Catégories de tickets
CATEGORIES = [
    "Question produit",
    "Problème technique",
    "Demande de remboursement",
    "Plainte",
    "Autre",
]

# Priorités
PRIORITIES = {
    "haute"  : "🔴 Haute",
    "moyenne": "🟡 Moyenne",
    "basse"  : "🟢 Basse",
}

# Ton des réponses générées
RESPONSE_TON = "Professionnel, empathique et solution-oriented"

# Langue des réponses
RESPONSE_LANGUE = "Français"

# Signature automatique
SIGNATURE = "L'équipe Support"