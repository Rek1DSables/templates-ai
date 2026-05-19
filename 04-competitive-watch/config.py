# ============================================================
# CONFIG — Agent de veille concurrentielle
# Modifier uniquement ce fichier pour adapter au client
# ============================================================

# Nom affiché dans l'interface
APP_TITLE = "🔍 Agent de veille concurrentielle"
APP_SUBTITLE = "Analysez vos concurrents et recevez un rapport structuré automatiquement."

# Modèle Anthropic utilisé
MODEL = "claude-haiku-4-5-20251001"

# Nombre de résultats web par concurrent
SEARCH_RESULTS = 5

# Sections du rapport généré
RAPPORT_SECTIONS = [
    "Actualités récentes",
    "Nouveaux produits ou services",
    "Stratégie marketing détectée",
    "Points forts",
    "Points faibles",
    "Opportunités pour notre client",
]

# Langue du rapport
RAPPORT_LANGUE = "Français"

# Tonalité du rapport
RAPPORT_TON = "Professionnel et analytique"

# Longueur du rapport
RAPPORT_LENGTHS = {
    "Court"  : "1-2 points par section, 1 phrase par point",
    "Moyen"  : "3-4 points par section, 2 phrases par point",
    "Long"   : "5 points minimum par section, développé et détaillé",
}