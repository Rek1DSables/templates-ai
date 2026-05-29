# 08 — Agent Email Entrant

Pipeline de traitement automatique des emails entrants. LangGraph orchestre 3 nœuds : collecte Gmail ou mode démo, classification et génération de réponses, envoi automatique optionnel. Tri par priorité, détection spam, réponses suggérées.

## Stack

- **LangGraph** — orchestration avec routeur conditionnel
- **Anthropic Claude** — classification, analyse sentiment, génération réponses
- **Gmail API** — lecture emails non lus + envoi réponses
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Mode démo (5 emails fictifs) ou mode Gmail réel
- Classification en 7 catégories (Support, Commercial, Réclamation, Partenariat, Candidature, Spam, Autre)
- 4 niveaux de priorité avec tri automatique
- Analyse de sentiment (positif / neutre / négatif)
- Résumé et action recommandée pour chaque email
- Réponse suggérée prête à envoyer
- Envoi automatique optionnel via Gmail API
- Détection et mise en bas de liste du spam
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
08-agent-email-entrant/
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
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## Gmail OAuth2

```powershell
copy C:\Users\steph\projets-python\credentials.json .
copy C:\Users\steph\projets-python\token.json .
```

## Test rapide

Lancer en mode démo (toggle activé par défaut) — 5 emails de test inclus couvrant tous les cas : support urgent, demande commerciale, réclamation, partenariat, spam.

## Modèle utilisé

`claude-haiku-4-5-20251001`