# 04 — Agent Reporting & Alertes

Pipeline de reporting business automatisé. LangGraph orchestre 3 nœuds : analyse des KPIs, génération de recommandations stratégiques, envoi du rapport par email. Dashboard Plotly interactif, alertes automatiques, export PDF.

## Stack

- **LangGraph** — orchestration avec routeur conditionnel
- **Anthropic Claude Sonnet** — génération des recommandations
- **Plotly** — dashboard KPIs interactif
- **FPDF2** — export PDF du rapport
- **Gmail API** — envoi rapport par email (optionnel)
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 8 KPIs configurables (CA, croissance, MRR, churn, NPS, CAC, conversion, nouveaux clients)
- Score de santé global 0-100
- Alertes automatiques sur les KPIs hors seuil
- 5 recommandations prioritaires avec action, impact, délai, responsable et KPI de suivi
- Dashboard Plotly interactif
- Export PDF du rapport complet
- Envoi automatique par email via Gmail API (optionnel)
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
04-agent-reporting-alertes/
├── app.py              # Interface Streamlit + dashboard Plotly
├── graph.py            # LangGraph 3 nœuds + routeur
├── config.py           # Configuration centralisée
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

## Gmail OAuth2

```powershell
copy C:\Users\steph\projets-python\credentials.json .
copy C:\Users\steph\projets-python\token.json .
```

## Données de test

Laisser les valeurs par défaut et renseigner :
- Entreprise : Acme Corp
- Secteur : SaaS B2B
- Période : Hebdomadaire

## Modèles utilisés

- `claude-haiku-4-5-20251001` — analyse KPIs
- `claude-sonnet-4-6` — génération recommandations