# 02 — Agent Content Marketing & Newsletters

Pipeline de génération de contenu multicanal avec envoi newsletter optionnel. LangGraph orchestre 3 nœuds : recherche de contexte web, génération de contenu adapté au canal, envoi email via Gmail API.

## Stack

- **LangGraph** — orchestration avec routeur conditionnel
- **Anthropic Claude Sonnet** — génération de contenu long
- **Serper** — recherche web pour contexte et tendances
- **Gmail API** — envoi newsletter par email
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 7 canaux : Article blog, Post LinkedIn, Thread Twitter/X, Newsletter, Email marketing, Script YouTube, Carrousel Instagram
- 6 tons : Professionnel, Educatif, Inspirant, Humoristique, Direct, Storytelling
- 4 longueurs : Court / Moyen / Long / Très long
- Recherche web automatique pour enrichir le contenu avec les tendances actuelles
- Envoi direct par email via Gmail API (optionnel)
- Export TXT du contenu généré
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
02-agent-content-marketing-newsletters/
├── app.py              # Interface Streamlit
├── graph.py            # LangGraph 3 nœuds + routeur
├── config.py           # Configuration centralisée
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
SERPER_API_KEY=ta_clé_serper
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## Gmail OAuth2

Copier `credentials.json` et `token.json` depuis le projet source :

```powershell
copy C:\Users\steph\projets-python\credentials.json .
copy C:\Users\steph\projets-python\token.json .
```

## Données de test

- Sujet : L'IA générative dans les PME en 2025
- Canal : Newsletter
- Ton : Educatif
- Audience : Dirigeants de PME

## Modèles utilisés

- `claude-haiku-4-5-20251001` — recherche et traitement
- `claude-sonnet-4-6` — génération de contenu long