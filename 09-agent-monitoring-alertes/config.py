# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE_ALERTES = "monitoring_alertes"
SUPABASE_TABLE_METRIQUES = "monitoring_metriques"

# Gmail
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Niveaux d'alerte
NIVEAUX_ALERTE = {
    "critique": {"icone": "🔴", "couleur": "red", "sla_minutes": 15},
    "eleve": {"icone": "🟠", "couleur": "orange", "sla_minutes": 60},
    "moyen": {"icone": "🟡", "couleur": "yellow", "sla_minutes": 240},
    "info": {"icone": "🔵", "couleur": "blue", "sla_minutes": 1440},
}

# Types de métriques surveillées
TYPES_METRIQUES = [
    "Performance applicative (API, temps de réponse)",
    "KPIs business (CA, conversion, churn)",
    "Infrastructure (CPU, mémoire, disque)",
    "Qualité des données (anomalies, doublons)",
    "Sécurité (tentatives connexion, accès suspects)",
    "Finance (trésorerie, factures, marges)",
    "Support client (tickets, SLA, satisfaction)",
]

# Canaux de notification
CANAUX_NOTIFICATION = ["Email Gmail", "Supabase (log)", "Interface Streamlit"]

# Seuils par défaut
SEUILS_DEFAUT = {
    "taux_erreur_api": {"seuil": 5.0, "unite": "%", "direction": "above"},
    "temps_reponse_ms": {"seuil": 2000, "unite": "ms", "direction": "above"},
    "taux_conversion": {"seuil": 2.0, "unite": "%", "direction": "below"},
    "churn_mensuel": {"seuil": 5.0, "unite": "%", "direction": "above"},
    "cpu_usage": {"seuil": 85.0, "unite": "%", "direction": "above"},
    "memoire_usage": {"seuil": 90.0, "unite": "%", "direction": "above"},
    "ca_journalier": {"seuil": 1000, "unite": "EUR", "direction": "below"},
    "nb_tickets_ouverts": {"seuil": 20, "unite": "", "direction": "above"},
}

# SQL Supabase
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS monitoring_alertes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    niveau TEXT,
    metrique TEXT,
    valeur_actuelle NUMERIC,
    seuil NUMERIC,
    message TEXT,
    cause_probable TEXT,
    action_recommandee TEXT,
    statut TEXT DEFAULT 'ouverte',
    acquittee_par TEXT,
    acquittee_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS monitoring_metriques (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    metrique TEXT,
    valeur NUMERIC,
    unite TEXT,
    contexte TEXT
);
"""