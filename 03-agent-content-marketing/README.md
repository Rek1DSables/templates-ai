# 03 — Agent Content Marketing Multicanal AI

Pipeline de génération de contenu marketing multicanal. LangGraph orchestre 4 agents en séquence : recherche web contextuelle, rédaction article de blog SEO, adaptation LinkedIn, adaptation thread Twitter/X. Export PDF des 3 formats inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 4 agents
- **Anthropic Claude** — rédaction multicanal
- **Serper** — recherche web pour contextualiser le contenu
- **FPDF2** — export PDF des 3 formats
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Recherche web automatique pour ancrer le contenu dans l'actualité 2025
- Article de blog 600-800 mots optimisé SEO avec structure H1/H2
- Post LinkedIn avec accroche, storytelling, emojis et hashtags
- Thread Twitter/X 5-7 tweets numérotés
- Ton et cible configurables
- Export PDF des 3 formats en un clic
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
03-agent-content-marketing/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph 4 agents
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

- Secteur : Tech / SaaS
- Ton : Professionnel
- Cible : Dirigeants PME
- Sujet : L'impact de l'IA generative sur la productivite des equipes marketing en 2025

## Modèle utilisé

`claude-haiku-4-5-20251001`