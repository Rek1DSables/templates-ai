# 12 — Agent Intégration SI & Webhook

Pipeline multi-agents d'intégration de systèmes d'information. 4 agents spécialisés : réception et validation avec déduplication idempotente, transformation et mapping multi-destinations, envoi avec retry configurable et dead letter queue, rapport d'intégration.

## Stack

- **LangGraph** — orchestration 4 agents + routeur conditionnel
- **Anthropic Claude Sonnet** — rapport et recommandations
- **Anthropic Claude Haiku** — validation payload et mapping
- **Supabase** — persistance événements et dead letter queue
- **Requests** — envoi HTTP vers destinations réelles
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Réception & Validation | Déduplication SHA-256, validation IA du payload |
| Agent Transformation & Mapping | Adaptation format par destination, enrichissements |
| Agent Envoi & Retry | Retry configurable, dead letter automatique |
| Agent Rapport | Métriques d'intégration, recommandations |

## Patterns implémentés

- **Idempotency** — event_id SHA-256 pour éviter les doublons
- **Retry** — 3 stratégies : exponential / linear / fixed
- **Dead Letter Queue** — persistance Supabase des événements en échec
- **Routeur conditionnel** — payload invalide → dead letter direct
- **Multi-destinations** — un payload → N systèmes cibles

## Fonctionnalités

- 5 types d'intégration : webhook, polling, event-driven, ETL, sync bidirectionnelle
- 7 systèmes cibles : CRM, ERP, Slack, BDD, Email, Webhook, REST API
- 4 payloads de démo : Stripe paiement, GitHub PR, CRM lead, alerte monitoring
- Validation IA du payload entrant avec score qualité
- Transformation et mapping adapté par destination
- Retry avec backoff exponentiel configurable
- Dead Letter Queue avec détail erreur et payload
- Mode démo (envois simulés) ou réel (HTTP)
- Export audit trail JSON + rapport complet
- Retry automatique (3 tentatives, 5s)

## Structure

```
12-agent-integration-si-webhook/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph 4 agents + routeur
├── config.py       # Types, stratégies retry, payloads démo
├── requirements.txt
├── .env
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Variables d'environnement

```
ANTHROPIC_API_KEY=ta_clé_ici
SUPABASE_URL=ton_url_supabase
SUPABASE_KEY=ta_clé_supabase
```

## Test rapide

Mode démo → Payload "Webhook Stripe — Paiement reçu" → CRM + Base de données → Lancer

## Modèles utilisés

- `claude-haiku-4-5-20251001` — validation et mapping
- `claude-sonnet-4-6` — rapport et recommandations