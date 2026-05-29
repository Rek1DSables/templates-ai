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

# Types de contrats
TYPES_CONTRATS = [
    "Contrat de prestation de services",
    "Contrat de vente",
    "Contrat de licence logicielle",
    "Accord de partenariat",
    "Contrat de distribution",
    "NDA / Accord de confidentialité",
    "Contrat de travail",
    "Contrat de sous-traitance",
]

# Niveaux de risque
NIVEAUX_RISQUE = {
    "critique": "🔴",
    "eleve": "🟠",
    "moyen": "🟡",
    "faible": "🟢",
}

# Modes
MODES = [
    "Analyser un contrat existant",
    "Générer un nouveau contrat",
    "Analyser ET générer une version améliorée",
]

# Clauses obligatoires par type
CLAUSES_OBLIGATOIRES = {
    "Contrat de prestation de services": [
        "Objet et périmètre",
        "Durée et renouvellement",
        "Prix et modalités de paiement",
        "Obligations du prestataire",
        "Obligations du client",
        "Responsabilité et assurance",
        "Propriété intellectuelle",
        "Confidentialité",
        "Résiliation",
        "Loi applicable",
    ],
    "NDA / Accord de confidentialité": [
        "Définition des informations confidentielles",
        "Obligations de confidentialité",
        "Durée",
        "Exclusions",
        "Sanctions",
        "Loi applicable",
    ],
}

# SQL Supabase
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS contrats (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nom TEXT,
    type_contrat TEXT,
    score_risque INTEGER,
    nb_risques_critiques INTEGER,
    statut TEXT DEFAULT 'analyse',
    contenu_original TEXT,
    contenu_ameliore TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""