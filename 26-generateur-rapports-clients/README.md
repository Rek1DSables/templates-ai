# 26 — Générateur de Rapports Clients AI

Pipeline de génération de rapports clients professionnels pour freelances et consultants. LangGraph orchestre 3 agents en séquence : résumé exécutif valorisant, analyse de performance avec scoring, rédaction du rapport complet 7 sections. Export PDF inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — résumé, analyse performance, rapport complet
- **Supabase** — archivage des rapports
- **FPDF2** — export PDF professionnel
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Formulaire mission : prestataire, client, type, période, date
- Saisie des réalisations, KPIs, problèmes et prochaines étapes
- Résumé exécutif valorisant automatique
- Analyse de performance avec score /10 et tableaux KPIs
- Rapport complet 7 sections (résumé, réalisations, KPIs, analyse, points d'attention, prochaines étapes, conclusion)
- Export PDF téléchargeable
- Archivage Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
26-generateur-rapports-clients/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph 3 agents
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
CREATE TABLE rapports_clients (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prestataire_nom TEXT,
    client_nom TEXT,
    client_entreprise TEXT,
    type_mission TEXT,
    periode TEXT,
    date_rapport TEXT,
    rapport TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Votre nom : Jean Martin
- Entreprise cliente : Acme Corp
- Contact client : Marie Dupont
- Type : AI / Automatisation / Mensuel
- Taches : Developpement agent IA LangGraph, Integration Supabase, Deploiement Streamlit
- KPIs : 95% precision, -95% temps traitement, 47 leads traites, satisfaction 9/10

## Modèle utilisé

`claude-haiku-4-5-20251001`