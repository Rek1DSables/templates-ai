# 📄 05 — Résumeur automatique de documents

Pipeline LangGraph qui extrait et résume automatiquement le contenu de vos PDFs.

## Fonctionnement

1. L'utilisateur uploade un PDF
2. Le pipeline extrait et découpe le texte
3. L'agent génère un résumé selon le format choisi
4. Téléchargement du résumé en un clic

## Stack technique

- **LangGraph** — orchestration du pipeline
- **Anthropic Claude Haiku** — moteur de résumé
- **PyPDF** — extraction du texte PDF
- **Streamlit** — interface utilisateur

## Installation

    pip install -r requirements.txt

## Configuration

Tout se passe dans `config.py` :
- `OUTPUT_FORMATS` — formats de sortie disponibles
- `OUTPUT_LANGUE` — langue du résumé
- `CHUNK_SIZE` — taille des chunks de texte
- `MODEL` — modèle Anthropic utilisé

## Lancement

    streamlit run app.py

## Variables d'environnement

Créer un fichier `.env` :

    ANTHROPIC_API_KEY=ta_clé_ici

## Adaptation client

1. Modifier les formats de sortie dans `config.py`
2. Renseigner la clé API dans `.env`
3. Lancer l'app