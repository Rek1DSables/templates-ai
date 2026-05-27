# 29 — Chatbot Multilingue AI

Chatbot avec détection automatique de la langue et réponse dans la langue de l'utilisateur. LangGraph orchestre 2 agents : détection de langue, génération de réponse contextualisée depuis la base de connaissance. Historique de conversation persistant en session. Archivage Supabase.

## Stack

- **LangGraph** — orchestration des 2 agents
- **Anthropic Claude** — détection langue + génération réponse
- **Supabase** — archivage des conversations
- **Streamlit** — interface chat native

## Fonctionnalités

- Détection automatique de la langue (11 langues supportées)
- Réponse toujours dans la langue de l'utilisateur
- Base de connaissance configurable depuis la sidebar
- Historique de conversation persistant en session
- Interface chat native Streamlit
- Réinitialisation conversation en un clic
- Archivage Supabase de chaque échange
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
29-chatbot-multilingue/
├── app.py          # Interface Streamlit chat
├── graph.py        # LangGraph 2 agents
├── config.py       # Configuration + base connaissance defaut
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
CREATE TABLE chatbot_conversations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    message TEXT,
    langue_detectee TEXT,
    reponse TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- FR : Comment fonctionne votre produit ?
- EN : What are your pricing plans ?
- ES : Cuanto cuesta el producto ?
- DE : Wie kann ich den Support kontaktieren ?

## Modèle utilisé

`claude-haiku-4-5-20251001`