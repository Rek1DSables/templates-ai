# 09 — Agent Monitoring & Alertes

Pipeline multi-agents de monitoring en temps réel. 4 agents spécialisés : détection des violations de seuils, analyse causale et corrélations, génération d'alertes graduées, rapport et notification Gmail. Dashboard avec gauge de santé et alertes par niveau.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — rapport et analyse causale
- **Anthropic Claude Haiku** — détection violations et génération alertes
- **Supabase** — persistance des alertes et métriques
- **Plotly** — gauge de santé + visualisations
- **Gmail API** — notification email si alertes critiques
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Détection | Compare métriques vs seuils, calcule écarts et niveaux |
| Agent Analyse Causale | Corrélations, cause racine, score de santé 0-100 |
| Agent Génération Alertes | Alerte structurée par violation, sauvegarde Supabase |
| Agent Rapport & Notification | Rapport synthétique + envoi Gmail optionnel |

## Fonctionnalités

- 8 métriques pré-configurées (API, conversion, churn, CPU, mémoire, CA, tickets)
- 4 niveaux d'alerte : critique (SLA 15min) / élevé (60min) / moyen (4h) / info (24h)
- Score de santé global 0-100 avec gauge Plotly
- Analyse causale et corrélations entre violations
- Actions recommandées avec responsable et délai
- Persistance alertes dans Supabase
- Notification email Gmail si alertes critiques
- Mode démo (8 métriques avec violations) ou configuration manuelle
- Export alertes CSV + rapport JSON complet
- Retry automatique (3 tentatives, 5s)

## Structure

```
09-agent-monitoring-alertes/
├── app.py              # Interface Streamlit + gauge
├── graph.py            # LangGraph 4 agents
├── config.py           # Seuils, niveaux alertes, SQL
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

## Données de test

Mode démo activé par défaut — 8 métriques avec violations intentionnelles :
- taux_erreur_api : 12.5% (seuil 5%)
- temps_reponse_ms : 3200ms (seuil 2000ms)
- taux_conversion : 1.2% (seuil 2%)
- churn_mensuel : 8.5% (seuil 5%)
- cpu_usage : 92% (seuil 85%)
- ca_journalier : 450€ (seuil 1000€)
- nb_tickets_ouverts : 35 (seuil 20)

## Modèles utilisés

- `claude-haiku-4-5-20251001` — détection et alertes
- `claude-sonnet-4-6` — analyse causale et rapport