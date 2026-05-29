# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Supabase CRM
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_PROSPECTS = "sdr_prospects"
SUPABASE_TABLE_SEQUENCES = "sdr_sequences"

# Serper
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# ICP — Ideal Customer Profile
SECTEURS_CIBLES = [
    "SaaS B2B",
    "Fintech",
    "Juridique / Cabinet d'avocats",
    "Finance / Gestion de patrimoine",
    "Industrie / Manufacturing",
    "Santé / Pharma",
    "Conseil / ESN",
    "E-commerce",
    "Immobilier",
    "Autre",
]

TAILLES_ENTREPRISE = [
    "TPE (1-10 salariés)",
    "PME (10-250 salariés)",
    "ETI (250-5000 salariés)",
    "Grand compte (5000+)",
]

POSTES_CIBLES = [
    "CEO / Directeur Général",
    "CTO / Directeur Technique",
    "CFO / Directeur Financier",
    "DSI / Responsable IT",
    "Directeur Commercial",
    "Directeur Marketing",
    "DRH / Responsable RH",
    "Directeur des Opérations",
    "Responsable Achats",
    "Autre",
]

OBJECTIFS_SEQUENCE = [
    "Prise de rendez-vous découverte",
    "Démonstration produit",
    "Envoi proposition commerciale",
    "Réactivation prospect froid",
    "Upsell client existant",
]

# Scoring ICP
SCORE_SEUILS = {
    "hot": 75,
    "warm": 50,
    "cold": 0,
}

# SQL Supabase
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS sdr_prospects (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nom TEXT,
    prenom TEXT,
    email TEXT,
    entreprise TEXT,
    poste TEXT,
    secteur TEXT,
    taille_entreprise TEXT,
    site_web TEXT,
    linkedin TEXT,
    score_icp INTEGER DEFAULT 0,
    segment TEXT DEFAULT 'cold',
    signaux_business TEXT,
    resume_enrichi TEXT,
    statut TEXT DEFAULT 'nouveau',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sdr_sequences (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    prospect_email TEXT,
    etape INTEGER,
    sujet TEXT,
    corps TEXT,
    statut TEXT DEFAULT 'planifie',
    envoye_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
"""