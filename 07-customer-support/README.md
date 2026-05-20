# 🎧 07 — Agent Support Client Multi-Canal

Pipeline LangGraph qui classifie automatiquement les tickets, génère une réponse draft et escalade les cas complexes.

## Fonctionnement

1. Le client soumet son message
2. L'agent classifie le ticket (catégorie, priorité, score de confiance)
3. Routing automatique : réponse automatique ou escalade humaine
4. Génération d'une réponse draft professionnelle
5. Sauvegarde dans Supabase + historique

## Stack technique

- **LangGraph** — orchestration avec routing conditionnel
- **Anthropic Claude Haiku** — classification et génération
- **Supabase** — persistance des tickets
- **Streamlit** — interface utilisateur

## Installation

    pip install -r requirements.txt

## Configuration

Tout se passe dans `config.py` :
- `SCORE_AUTO_REPONSE` — seuil réponse automatique (défaut : 7)
- `SCORE_ESCALADE` — seuil escalade humaine (défaut : 4)
- `CATEGORIES` — catégories de tickets
- `RESPONSE_TON` — ton des réponses générées
- `SIGNATURE` — signature automatique
- `MODEL` — modèle Anthropic utilisé

## Lancement

    streamlit run app.py

## Variables d'environnement

Créer un fichier `.env` :

    ANTHROPIC_API_KEY=ta_clé_ici
    SUPABASE_URL=ton_url_supabase
    SUPABASE_KEY=ta_clé_supabase

## Table Supabase requise

```sql
CREATE TABLE tickets (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    nom TEXT, email TEXT, message TEXT,
    category TEXT, priority TEXT,
    score INTEGER, response TEXT,
    escalade BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Adaptation client

1. Modifier les catégories et seuils dans `config.py`
2. Créer la table `tickets` dans Supabase
3. Renseigner les credentials dans `.env`
4. Lancer l'app