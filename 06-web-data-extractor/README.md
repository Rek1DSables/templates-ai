# 🌐 06 — Extracteur de données web

Pipeline LangGraph qui scrape et structure automatiquement le contenu de n'importe quelle page web.

## Fonctionnement

1. L'utilisateur saisit une URL
2. Le pipeline scrape et nettoie le contenu de la page
3. L'agent structure les données selon le format choisi
4. Téléchargement des données en un clic

## Stack technique

- **LangGraph** — orchestration du pipeline
- **Anthropic Claude Haiku** — moteur d'extraction et structuration
- **BeautifulSoup** — scraping et nettoyage HTML
- **Streamlit** — interface utilisateur

## Installation

    pip install -r requirements.txt

## Configuration

Tout se passe dans `config.py` :
- `EXTRACT_FORMATS` — formats d'extraction disponibles
- `OUTPUT_LANGUE` — langue de sortie
- `MAX_CHARS` — nombre maximum de caractères analysés
- `MODEL` — modèle Anthropic utilisé

## Lancement

    streamlit run app.py

## Variables d'environnement

Créer un fichier `.env` :

    ANTHROPIC_API_KEY=ta_clé_ici

## Adaptation client

1. Modifier les formats d'extraction dans `config.py`
2. Renseigner la clé API dans `.env`
3. Lancer l'app