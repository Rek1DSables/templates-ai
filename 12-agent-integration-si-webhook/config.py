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

# Types d'intégrations supportées
TYPES_INTEGRATION = [
    "Webhook entrant → traitement → API sortante",
    "API polling → transformation → stockage",
    "Event-driven → multi-destinations",
    "ETL temps réel → validation → destination",
    "Synchronisation bidirectionnelle SI",
]

# Systèmes cibles simulés
SYSTEMES_CIBLES = [
    "CRM (HubSpot / Salesforce)",
    "ERP (SAP / Oracle)",
    "Slack / Teams",
    "Base de données (PostgreSQL / Supabase)",
    "Email (Gmail / SendGrid)",
    "Webhook custom",
    "REST API tierce",
]

# Stratégies de retry
STRATEGIES_RETRY = {
    "linear": {"max_attempts": 3, "delay_base": 5},
    "exponential": {"max_attempts": 5, "delay_base": 2},
    "fixed": {"max_attempts": 3, "delay_base": 10},
}

# Codes d'erreur et comportements
CODES_ERREUR = {
    200: ("success", "continuer"),
    201: ("created", "continuer"),
    400: ("bad_request", "dead_letter"),
    401: ("unauthorized", "alerter"),
    403: ("forbidden", "alerter"),
    404: ("not_found", "dead_letter"),
    429: ("rate_limit", "retry_backoff"),
    500: ("server_error", "retry"),
    503: ("unavailable", "retry_backoff"),
}

# Payloads de demo
PAYLOADS_DEMO = {
    "Webhook Stripe — Paiement reçu": {
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_3ABC123",
                "amount": 4900,
                "currency": "eur",
                "customer": "cus_ABC123",
                "metadata": {
                    "order_id": "ORD-2026-0892",
                    "product": "CRM Pro Annual",
                    "user_email": "client@acme.com"
                },
                "status": "succeeded",
                "created": 1748476800,
            }
        },
        "livemode": True,
    },
    "Webhook GitHub — Pull Request": {
        "action": "opened",
        "pull_request": {
            "number": 142,
            "title": "feat: ajout agent monitoring temps réel",
            "state": "open",
            "user": {"login": "dev-shark"},
            "base": {"ref": "main"},
            "head": {"ref": "feat/monitoring-agent"},
            "body": "Ajout d'un pipeline LangGraph pour le monitoring",
            "additions": 450,
            "deletions": 12,
        },
        "repository": {"full_name": "Rek1DSables/templates-ai"},
    },
    "Webhook CRM — Nouveau lead": {
        "event": "lead.created",
        "lead": {
            "id": "lead_2026_0445",
            "email": "prospect@fintech.fr",
            "nom": "Alexandre Petit",
            "entreprise": "FintechPlus",
            "poste": "CEO",
            "source": "LinkedIn",
            "score": 85,
            "created_at": "2026-05-29T14:30:00Z",
        },
    },
    "Event monitoring — Alerte critique": {
        "alert_id": "ALT-2026-0123",
        "severity": "critical",
        "metric": "cpu_usage",
        "value": 95.2,
        "threshold": 85.0,
        "service": "api-gateway-prod",
        "timestamp": "2026-05-29T14:35:00Z",
        "environment": "production",
    },
}

# SQL Supabase
SQL_SETUP = """
CREATE TABLE IF NOT EXISTS si_events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id TEXT UNIQUE,
    type_integration TEXT,
    payload_original JSONB,
    payload_transforme JSONB,
    statut TEXT DEFAULT 'recu',
    tentatives INTEGER DEFAULT 0,
    destination TEXT,
    reponse_destination TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS si_dead_letter (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    event_id TEXT,
    erreur TEXT,
    payload JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
"""