# 04 — Agent SDR / Revenue

Pipeline multi-agents de prospection commerciale B2B autonome. 4 agents spécialisés : enrichissement web par prospect, scoring ICP, génération de séquence 3 emails personnalisés, envoi Gmail du premier email.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — génération séquences emails personnalisées
- **Anthropic Claude Haiku** — scoring ICP et enrichissement
- **Serper** — recherche web de signaux business par prospect
- **Supabase** — CRM prospects et séquences
- **Gmail API** — envoi premier email de la séquence
- **Plotly** — visualisation scores ICP
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Enrichissement | Recherche web (Serper) + qualification IA + signaux business |
| Agent Scoring | Score ICP 0-100, segmentation hot/warm/cold, sauvegarde Supabase |
| Agent Séquence | 3 emails personnalisés par prospect (hot + warm uniquement) |
| Agent Envoi | Premier email via Gmail (optionnel) |

## Fonctionnalités

- Configuration ICP : secteurs, postes et tailles d'entreprise cibles
- Enrichissement automatique via recherche web Serper par prospect
- Scoring ICP 0-100 avec segmentation hot (75+) / warm (50-74) / cold (<50)
- Détection de signaux business (levées de fonds, recrutements, actualités)
- Séquence 3 emails : premier contact + relance J+5 + breakup J+12
- Emails ultra-personnalisés selon segment, signaux et angle d'approche
- Sauvegarde automatique prospects et séquences dans Supabase
- Mode démo (5 prospects fictifs) ou upload CSV
- Template CSV téléchargeable
- Export prospects qualifiés CSV + pipeline complet JSON
- Retry automatique (3 tentatives, 5s)

## Structure

```
04-agent-sdr-revenue/
├── app.py              # Interface Streamlit + visualisations
├── graph.py            # LangGraph 4 agents
├── config.py           # ICP, scoring, SQL setup
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
SERPER_API_KEY=ta_clé_serper
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## Gmail OAuth2

```powershell
copy C:\Users\steph\projets-python\credentials.json .
copy C:\Users\steph\projets-python\token.json .
```

## Modèles utilisés

- `claude-haiku-4-5-20251001` — scoring ICP et enrichissement
- `claude-sonnet-4-6` — génération séquences emails