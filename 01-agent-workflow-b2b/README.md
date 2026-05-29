# 01 — Agent Workflow B2B

Pipeline multi-agents de traitement automatique des emails entrants avec intégration CRM complète. 5 agents spécialisés en séquence : lookup CRM, classification, mise à jour CRM, génération de réponse, envoi Gmail.

## Stack

- **LangGraph** — orchestration séquentielle 5 agents + routeur spam
- **Anthropic Claude Sonnet** — génération réponse contextualisée
- **Anthropic Claude Haiku** — classification, extraction entités
- **Supabase** — CRM (contacts, tickets, interactions)
- **Gmail API** — envoi réponse automatique
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent CRM Lookup | Recherche contact, récupère historique interactions |
| Agent Classification | Catégorie, priorité, sentiment, entités extraites |
| Agent CRM Update | Crée ticket, met à jour contact, programme relance |
| Agent Réponse | Génère réponse contextualisée avec numéro ticket |
| Agent Gmail | Envoie la réponse (réel) ou simule (démo) |

## Fonctionnalités

- 8 catégories de classification (Support, Commercial, Réclamation, Partenariat, RH, Spam...)
- 4 niveaux de priorité avec SLA automatique (2h / 8h / 24h / 72h)
- Routing automatique vers l'équipe concernée
- Création automatique de ticket avec référence unique
- Programmation automatique de relance selon SLA
- Historique interactions récupéré depuis Supabase
- Réponse personnalisée selon segment client et valeur
- Mode démo (4 emails de test) ou Gmail réel
- Audit trail complet horodaté
- Export audit trail JSON

## Structure

```
01-agent-workflow-b2b/
├── app.py              # Interface Streamlit
├── graph.py            # LangGraph 5 agents + routeur
├── config.py           # Configuration + SQL setup
├── requirements.txt
├── .env
├── credentials.json    # Gmail OAuth2 (non versionné)
├── token.json          # Gmail token (non versionné)
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
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## Setup Supabase

Exécuter le SQL disponible dans l'interface (onglet "Setup Supabase") pour créer les 3 tables : crm_contacts, crm_tickets, crm_interactions.

## Gmail OAuth2

```powershell
copy C:\Users\steph\projets-python\credentials.json .
copy C:\Users\steph\projets-python\token.json .
```

## Données de test

4 emails de demo inclus : urgence technique, prospection commerciale, réclamation formelle, spam.

## Modèles utilisés

- `claude-haiku-4-5-20251001` — classification et extraction
- `claude-sonnet-4-6` — génération réponse