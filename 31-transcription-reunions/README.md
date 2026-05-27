# 31 — Transcription & Résumé de Réunions AI

Pipeline d'analyse automatique de transcriptions de réunions. LangGraph orchestre 3 agents Claude en séquence : nettoyage du transcript brut, génération d'un résumé exécutif structuré, extraction des action items avec responsables et priorités. Archivage Supabase de chaque analyse.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — nettoyage, résumé et extraction d'action items
- **Supabase** — archivage des analyses de réunions
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Saisie du transcript par texte libre ou upload de fichier .txt
- Nettoyage et structuration du transcript brut (intervenants, ponctuation, répétitions)
- Résumé exécutif en 5 sections (contexte, points clés, décisions, points en suspens, prochaine étape)
- Extraction des action items avec responsable, deadline et priorité
- Résultats affichés en 3 onglets
- Archivage complet dans Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
31-transcription-reunions/
├── app.py          # Interface Streamlit + Supabase
├── graph.py        # LangGraph 3 noeuds sequentiels
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
CREATE TABLE reunions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    titre TEXT,
    date_reunion TEXT,
    participants TEXT,
    transcript_brut TEXT,
    transcript_nettoye TEXT,
    resume TEXT,
    action_items TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Titre : Revue de sprint Q2
- Date : 27/05/2026
- Participants : Alice (PO), Bob (Dev), Claire (Design)
- Transcript : texte brut de réunion collé dans le champ texte

## Modèle utilisé

`claude-haiku-4-5-20251001`