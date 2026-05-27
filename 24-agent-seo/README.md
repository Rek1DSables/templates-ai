# 25 — Agent SEO AI

Pipeline d'audit SEO complet. LangGraph orchestre 4 agents en séquence : scraping technique de la page (title, meta, H1/H2/H3, images, liens), analyse des mots-clés via Serper, analyse concurrentielle, génération du rapport avec plan d'action 30/60/90 jours. Export PDF inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 4 agents
- **Anthropic Claude** — analyse technique, mots-clés, concurrence, rapport
- **BeautifulSoup** — scraping technique de la page
- **Serper** — analyse SERP et concurrence
- **FPDF2** — export PDF du rapport
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Scraping automatique : title, meta description, H1/H2/H3, images sans alt, liens
- Score SEO global 0-100
- Analyse technique détaillée avec recommandations correctives
- Analyse de positionnement pour chaque mot-clé cible
- Analyse concurrentielle avec identification des failles
- Rapport structuré : problèmes critiques, optimisations, stratégie mots-clés, plan 30/60/90 jours
- Export PDF complet téléchargeable
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
25-agent-seo/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph 4 agents + scraper
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
```

## Données de test

- URL : https://anthropic.com
- Type : SaaS / Application
- Secteur : Tech / SaaS
- Mots-cles : Claude AI, LLM API, AI assistant

## Modèle utilisé

`claude-haiku-4-5-20251001`