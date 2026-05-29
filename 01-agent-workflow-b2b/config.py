# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Supabase (CRM interne)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_CONTACTS = "crm_contacts"
SUPABASE_TABLE_TICKETS = "crm_tickets"
SUPABASE_TABLE_INTERACTIONS = "crm_interactions"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.modify",
]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Categories workflow
CATEGORIES_WORKFLOW = [
    "Support client — Problème technique",
    "Support client — Facturation",
    "Demande commerciale — Nouveau prospect",
    "Demande commerciale — Upsell",
    "Réclamation formelle",
    "Partenariat",
    "RH / Candidature",
    "Spam / Non pertinent",
]

# Priorites
PRIORITES = {
    "critique": {"label": "🔴 Critique", "sla_heures": 2},
    "haute": {"label": "🟠 Haute", "sla_heures": 8},
    "normale": {"label": "🟡 Normale", "sla_heures": 24},
    "basse": {"label": "🟢 Basse", "sla_heures": 72},
}

# Equipes de routing
EQUIPES = {
    "Support client — Problème technique": "equipe_technique",
    "Support client — Facturation": "equipe_finance",
    "Demande commerciale — Nouveau prospect": "equipe_commercial",
    "Demande commerciale — Upsell": "equipe_commercial",
    "Réclamation formelle": "equipe_direction",
    "Partenariat": "equipe_direction",
    "RH / Candidature": "equipe_rh",
    "Spam / Non pertinent": None,
}

# SQL creation tables Supabase
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS crm_contacts (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    nom TEXT,
    entreprise TEXT,
    telephone TEXT,
    segment TEXT,
    valeur_client NUMERIC DEFAULT 0,
    nb_interactions INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    reference TEXT UNIQUE NOT NULL,
    contact_email TEXT,
    sujet TEXT,
    categorie TEXT,
    priorite TEXT,
    statut TEXT DEFAULT 'ouvert',
    equipe_assignee TEXT,
    sla_heures INTEGER,
    relance_programmee TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS crm_interactions (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    ticket_reference TEXT,
    contact_email TEXT,
    type TEXT,
    contenu TEXT,
    agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
"""