# ✍️ 03 — Générateur de contenu marketing

Pipeline CrewAI 3 agents qui produit articles, posts LinkedIn, newsletters et emails commerciaux à partir d'un brief.

## Fonctionnement

1. L'utilisateur saisit un brief + choisit le type, ton, langue et longueur
2. Agent Researcher — recherche les informations clés sur le sujet
3. Agent Writer — rédige le contenu selon le brief
4. Agent Editor — relit, corrige et livre la version finale
5. Téléchargement du contenu en un clic

## Stack technique

- **CrewAI** — orchestration multi-agents
- **Anthropic Claude Haiku** — moteur de génération
- **Serper** — recherche web en temps réel (optionnel)
- **Streamlit** — interface utilisateur

## Installation

    pip install -r requirements.txt

## Configuration

Tout se passe dans `config.py` :
- `CONTENT_TYPES` — types de contenu disponibles
- `TONES` — tonalités disponibles
- `LANGUAGES` — langues disponibles
- `LENGTHS` — longueurs disponibles
- `USE_WEB_SEARCH` — activer/désactiver la recherche web
- `MODEL` — modèle Anthropic utilisé

## Lancement

    streamlit run app.py

## Variables d'environnement

Créer un fichier `.env` :

    ANTHROPIC_API_KEY=ta_clé_ici
    SERPER_API_KEY=ta_clé_serper

## Adaptation client

1. Modifier les types de contenu et tonalités dans `config.py`
2. Renseigner les credentials dans `.env`
3. Lancer l'app