# 12 — Agent Scraping & Extraction

Pipeline d'extraction de données structurées depuis des URLs ou du texte brut. LangGraph orchestre 2 nœuds : scraping du contenu web, extraction IA des données selon le type choisi. Export JSON et CSV inclus.

## Stack

- **LangGraph** — orchestration séquentielle
- **Anthropic Claude** — extraction structurée des données
- **BeautifulSoup** — scraping et nettoyage HTML
- **Pandas** — structuration et export CSV
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 3 modes : URL unique, liste d'URLs (max 5), texte brut
- 6 types d'extraction : Contacts, Produits, Offres d'emploi, Actualités, Avis clients, Données personnalisées
- Champs personnalisables en mode libre
- Affichage carte par carte avec source
- Export JSON et CSV
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
12-agent-scraping-extraction/
├── app.py          # Interface Streamlit + affichage cartes
├── graph.py        # LangGraph 2 nœuds
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

- URL : `https://news.ycombinator.com` / Type : Actualités
- URL : `https://www.leboncoin.fr` / Type : Produits
- Texte brut : coller une page de contacts ou d'annonces

## Modèle utilisé

`claude-haiku-4-5-20251001`