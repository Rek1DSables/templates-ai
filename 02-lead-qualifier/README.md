# 🎯 02 — Pipeline de Qualification de Leads

Agent LangGraph qui score automatiquement les prospects, les route selon leur potentiel et génère un email personnalisé.

## Fonctionnement

1. L'utilisateur saisit les infos du prospect + son message
2. L'agent score le lead de 0 à 10
3. Routing automatique : chaud / tiède / froid
4. Génération d'un email adapté à la catégorie
5. Sauvegarde dans Supabase + historique

## Stack technique

- **LangGraph** — orchestration du pipeline
- **Anthropic Claude Haiku** — scoring et génération email
- **Supabase** — persistance des leads
- **Streamlit** — interface utilisateur

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Tout se passe dans `config.py` :
- `SCORE_CHAUD` — seuil score chaud (défaut : 7)
- `SCORE_TIEDE` — seuil score tiède (défaut : 4)
- `CRITERES` — critères de scoring personnalisables
- `EMAIL_CHAUD_MOTS` — longueur max email chaud
- `EMAIL_TIEDE_MOTS` — longueur max email tiède
- `MODEL` — modèle Anthropic utilisé

## Lancement

```bash
streamlit run app.py
```

## Variables d'environnement

Créer un fichier `.env` avec les variables suivantes :

    ANTHROPIC_API_KEY=ta_clé_ici
    SUPABASE_URL=ton_url_supabase
    SUPABASE_KEY=ta_clé_supabase

    ## Adaptation client

1. Modifier les seuils et critères dans `config.py`
2. Créer une table `leads` dans Supabase
3. Renseigner les credentials dans `.env`
4. Lancer l'app