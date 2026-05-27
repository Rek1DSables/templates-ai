# 04 — Agent de Veille Multi-Sources AI

Pipeline de veille stratégique multi-sources. LangGraph orchestre 3 agents en séquence : collecte de sources via Serper (recherches adaptées au type de veille), analyse des signaux avec scoring d'alerte, génération d'un rapport structuré. Export PDF et archivage Supabase.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — analyse des signaux et génération du rapport
- **Serper** — collecte multi-sources en temps réel
- **Supabase** — archivage des rapports de veille
- **FPDF2** — export PDF du rapport
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 5 types de veille : Concurrentielle, Sectorielle, Réglementaire, Technologique, Multi-sources
- Jusqu'à 4 sujets surveillés simultanément
- Recherches Serper adaptées au type de veille + recherche complémentaire automatique
- Scoring d'alerte : Critique / Important / Informatif
- Rapport structuré en 4 sections
- Export PDF téléchargeable
- Historique des veilles dans la sidebar (Supabase)
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
04-agent-veille/
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
SERPER_API_KEY=ta_clé_serper
SUPABASE_URL=ton_url_supabase
SUPABASE_KEY=ta_clé_supabase
```

## SQL Supabase

```sql
CREATE TABLE veille (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    entreprise TEXT,
    secteur TEXT,
    type_veille TEXT,
    sujets TEXT,
    niveau_alerte TEXT,
    points_cles TEXT,
    rapport TEXT,
    date_veille TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Entreprise : Acme Corp
- Secteur : SaaS B2B
- Type : Concurrentielle
- Sujet 1 : Salesforce
- Sujet 2 : HubSpot
- Sujet 3 : IA CRM
- Sujet 4 : automatisation ventes

## Notes

- Rapport long : upgrade Sonnet prévu sur `generer_rapport` en passe polish
- Lancer depuis le dossier du template pour que le `.env` soit chargé correctement

## Modèle utilisé

`claude-haiku-4-5-20251001`