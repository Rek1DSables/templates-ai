# 03 — Agent Finance Close

Pipeline multi-agents de clôture financière. LangGraph orchestre 7 nœuds spécialisés : réconciliation des comptes, analyse des variances Budget vs Réel, génération des écritures de clôture, rapport narratif en 4 parties, audit log complet. Export PDF et JSON.

## Stack

- **LangGraph** — orchestration séquentielle 7 nœuds
- **Anthropic Claude Sonnet** — rapport narratif et disclosure
- **Anthropic Claude Haiku** — réconciliation, variances, journal entries
- **Plotly** — visualisation des variances
- **FPDF2** — export PDF rapport complet
- **Streamlit** — interface utilisateur

## Agents

| Agent | Rôle |
|-------|------|
| Agent Réconciliation | Détection écarts GL vs auxiliaire, anomalies, doublons |
| Agent Variance | Analyse Budget vs Réel, scoring performance |
| Agent Journal Entries | Génération écritures de régularisation et ajustement |
| Agent Disclosure x4 | Rapport narratif, checklist, conclusion, validation |

## Fonctionnalités

- Mode démo (données Acme Corp pré-remplies) ou saisie manuelle
- Réconciliation automatique multi-comptes avec détection anomalies
- Analyse variances Budget vs Réel avec seuils configurables (critique >5%, élevé >2%)
- Génération écritures de clôture équilibrées avec flag auto-reverse
- Rapport narratif complet en 4 sections
- Checklist de clôture en 8 points
- Score qualité global 0-100
- Audit log horodaté de toutes les décisions agents
- Export PDF rapport + JSON données complètes
- Retry automatique (3 tentatives, 5s)

## Normes supportées

IFRS, French GAAP (PCG), US GAAP

## Structure

```
03-agent-finance-close/
├── app.py          # Interface Streamlit + visualisations
├── graph.py        # LangGraph 7 nœuds
├── config.py       # Configuration centralisée
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
```

## Données de test

Mode démo activé par défaut — Acme Corp SAS / Mai 2026 / IFRS / EUR

## Modèles utilisés

- `claude-haiku-4-5-20251001` — réconciliation, variances, journal entries
- `claude-sonnet-4-6` — rapport narratif et conclusion