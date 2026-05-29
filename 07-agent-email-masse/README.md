# 10 — Agent Email en Masse

Pipeline de génération et d'envoi d'emails ultra-personnalisés à grande échelle. LangGraph orchestre 2 nœuds : génération Sonnet par contact, envoi Gmail. 3 modes d'import contacts : démo, CSV, saisie manuelle. Export JSON et CSV.

## Stack

- **LangGraph** — orchestration avec routeur conditionnel
- **Anthropic Claude Sonnet** — génération emails ultra-personnalisés
- **Gmail API** — envoi en masse avec délai anti-spam
- **Pandas** — gestion liste contacts
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 3 modes import : démo (5 contacts), upload CSV, saisie manuelle
- 8 objectifs : prospection, relance, upsell, invitation, annonce, réengagement, suivi post-démo, témoignage
- 5 tons : professionnel, chaleureux, urgent, éducatif, storytelling
- Personnalisation poussée : nom, prénom, entreprise, poste, secteur, info personnalisée
- Envoi Gmail réel avec délai entre envois (anti-spam)
- Export JSON et CSV des emails générés
- Template CSV téléchargeable
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
10-agent-email-masse/
├── app.py              # Interface Streamlit
├── graph.py            # LangGraph 2 nœuds + routeur
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

## Format CSV contacts

```csv
nom,prenom,email,entreprise,poste,secteur,info_perso
Martin,Sophie,sophie@acme.com,Acme Corp,CEO,SaaS B2B,Vient de lever 2M€
```

## Modèles utilisés

- `claude-sonnet-4-6` — génération emails personnalisés