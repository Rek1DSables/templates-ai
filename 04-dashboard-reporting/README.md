# 10 — Dashboard Reporting & Analytics AI

Pipeline de reporting business automatisé. LangGraph analyse les KPIs saisis, génère une analyse de performance avec scoring de santé, détecte les tendances et alertes, produit des recommandations actionnables. Dashboard Plotly interactif et export PDF inclus.

## Stack

- **LangGraph** — orchestration des 2 agents
- **Anthropic Claude** — analyse KPIs + recommandations
- **Plotly** — dashboard interactif (gauge + bar chart)
- **Pandas** — traitement des données
- **Supabase** — archivage des rapports
- **FPDF2** — export PDF
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 8 KPIs préconfigurés + 2 KPIs custom
- Score de santé global 0-100 avec gauge visuelle
- Bar chart des KPIs
- Analyse Claude : tendances, alertes, recommandations
- 5 recommandations prioritaires avec impact et délai
- Export PDF du rapport complet
- Archivage Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
10-dashboard-reporting/
├── app.py          # Interface Streamlit + Plotly + export PDF
├── graph.py        # LangGraph 2 agents
├── config.py       # Configuration centralisee
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

## SQL Supabase

```sql
CREATE TABLE rapports (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entreprise TEXT,
    secteur TEXT,
    periode TEXT,
    kpis TEXT,
    score_sante INT,
    tendances TEXT,
    alertes TEXT,
    recommandations TEXT,
    date_rapport TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

Les valeurs par défaut dans la sidebar suffisent — lancer directement avec "Acme Corp".

## Notes

- Recommandations longues : upgrade Sonnet prévu sur `generer_recommandations` en passe polish

## Modèle utilisé

`claude-haiku-4-5-20251001`