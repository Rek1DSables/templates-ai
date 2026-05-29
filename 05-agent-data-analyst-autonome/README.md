# 05 — Agent Data Analyst Autonome

Pipeline multi-agents d'analyse de données en langage naturel. 4 agents spécialisés : traduction question → SQL avec auto-correction, exécution et validation, analyse insights, commentaire exécutif. Connecté à SQLite en démo, PostgreSQL/Supabase/BigQuery en production.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — analyse insights et commentaire exécutif
- **Anthropic Claude Haiku** — génération SQL et auto-correction
- **SQLite** — base de données démo (remplaçable par PostgreSQL/Supabase)
- **Plotly** — visualisations automatiques (bar, line, pie, scatter)
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Text-to-SQL | Traduit la question en SQL valide, choisit le type de visualisation |
| Agent Exécution & Validation | Exécute le SQL, auto-corrige si erreur, retente |
| Agent Analyse Insights | Analyse résultats, détecte tendances et anomalies |
| Agent Commentaire Exécutif | Synthèse en 3 phrases pour le management |

## Ce qui différencie cet agent d'un LLM classique

- **Connecté à une vraie base SQL** — chiffres réels, pas inventés
- **Auto-correction** — si le SQL plante, l'agent se corrige et retente
- **Visualisation automatique** — choisit bar/line/pie/scatter selon la question
- **Audit trail** — chaque requête tracée horodatée
- **Production-ready** — connecter PostgreSQL, Supabase ou BigQuery en 2 lignes

## Fonctionnalités

- Questions en langage naturel sur n'importe quelle base SQL
- Génération SQL avec explication et type de visualisation recommandé
- Auto-correction SQL en cas d'erreur d'exécution
- 8 exemples de questions pré-configurés
- Base SQLite démo incluse (ventes + clients, 20 transactions)
- Visualisations automatiques Plotly selon le type de données
- Export CSV des résultats
- Audit trail JSON complet
- Retry automatique (3 tentatives, 5s)

## Structure

```
05-agent-data-analyst-autonome/
├── app.py          # Interface Streamlit + visualisations
├── graph.py        # LangGraph 4 agents + init DB
├── config.py       # Schéma démo, exemples questions
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
DB_TYPE=sqlite
DB_URL=demo.db
```

## Connexion base de production

Dans `graph.py`, remplacer `sqlite3.connect(DB_URL)` par :
```python
# PostgreSQL
import psycopg2
conn = psycopg2.connect(os.getenv("DATABASE_URL"))

# Supabase (PostgreSQL)
conn = psycopg2.connect(os.getenv("SUPABASE_DB_URL"))
```

## Questions de test

- Quel est le chiffre d'affaires total par région ?
- Quels sont les 5 produits les plus vendus ?
- Quel commercial a le meilleur CA ?
- Identifie les clients à risque de churn

## Modèles utilisés

- `claude-haiku-4-5-20251001` — génération et correction SQL
- `claude-sonnet-4-6` — analyse insights et commentaire exécutif