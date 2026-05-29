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

# Articles EU AI Act concernés
ARTICLES_EU_AI_ACT = {
    "Article 6 — Classification du risque": "Déterminer si le système est à risque élevé selon l'annexe III",
    "Article 9 — Système de gestion des risques": "Établir un processus continu d'identification et mitigation des risques",
    "Article 10 — Gouvernance des données": "Valider la qualité, représentativité et traçabilité des données d'entraînement",
    "Article 13 — Transparence": "Documenter les capacités, limites et performances du système",
    "Article 14 — Supervision humaine": "Implémenter des mécanismes de contrôle humain effectif",
    "Article 15 — Robustesse et cybersécurité": "Garantir précision, robustesse et protection contre les attaques",
    "Article 17 — Système qualité": "Mettre en place un système de management qualité documenté",
    "Article 72 — GPAI — Transparence": "Pour les modèles GPAI : documenter les données d'entraînement et évaluations",
}

# Niveaux de risque EU AI Act
NIVEAUX_RISQUE = {
    "Inacceptable": "🔴 Interdit — pratiques interdites par l'Article 5",
    "Élevé": "🟠 Haut risque — obligations strictes Articles 6-49",
    "Limité": "🟡 Risque limité — obligations de transparence Articles 50-52",
    "Minimal": "🟢 Risque minimal — pas d'obligation spécifique",
}

# Catégories de systèmes IA à risque élevé (Annexe III)
CATEGORIES_RISQUE_ELEVE = [
    "Biométrie et reconnaissance faciale",
    "Infrastructure critique (eau, gaz, électricité, transport)",
    "Éducation et formation professionnelle",
    "Emploi et gestion des travailleurs",
    "Accès aux services publics et prestations sociales",
    "Application de la loi",
    "Gestion des migrations et asile",
    "Administration de la justice",
    "Autre / Incertain",
]

# Secteurs
SECTEURS = [
    "Finance / Banque / Assurance",
    "Santé / Pharma",
    "RH / Recrutement",
    "Juridique / Compliance",
    "Éducation",
    "E-commerce / Retail",
    "Industrie / Manufacturing",
    "Transport / Logistique",
    "Secteur public",
    "SaaS / Tech B2B",
    "Autre",
]

# Deadlines EU AI Act 2026
DEADLINES = {
    "Février 2025": "Pratiques IA interdites (Article 5) — DÉJÀ EN VIGUEUR",
    "Août 2025": "Obligations GPAI (modèles à usage général) — DÉJÀ EN VIGUEUR",
    "Août 2026": "Systèmes IA à haut risque (Annexe III) — DEADLINE IMMINENTE",
    "Août 2027": "Systèmes IA à haut risque embarqués (produits existants)",
}