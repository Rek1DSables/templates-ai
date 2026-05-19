# 🔍 04 — Agent de veille concurrentielle

Pipeline CrewAI 3 agents qui analyse vos concurrents et produit un rapport structuré automatiquement.

## Fonctionnement

1. L'utilisateur saisit son entreprise, son secteur et ses concurrents
2. Agent Scout — recherche les informations récentes sur chaque concurrent
3. Agent Analyst — analyse les tendances et opportunités
4. Agent Reporter — rédige le rapport final structuré
5. Téléchargement du rapport en un clic

## Stack technique

- **CrewAI** — orchestration multi-agents
- **Anthropic Claude Haiku** — moteur d'analyse et de rédaction
- **Serper** — recherche web en temps réel
- **Streamlit** — interface utilisateur

## Installation

    pip install -r requirements.txt

## Configuration

Tout se passe dans `config.py` :
- `RAPPORT_SECTIONS` — sections du rapport à générer
- `RAPPORT_LANGUE` — langue du rapport
- `RAPPORT_TON` — tonalité du rapport
- `RAPPORT_LENGTHS` — options de longueur disponibles
- `SEARCH_RESULTS` — nombre de résultats web par concurrent
- `MODEL` — modèle Anthropic utilisé

## Lancement

    streamlit run app.py

## Variables d'environnement

Créer un fichier `.env` :

    ANTHROPIC_API_KEY=ta_clé_ici
    SERPER_API_KEY=ta_clé_serper

## Adaptation client

1. Modifier les sections et la langue dans `config.py`
2. Renseigner les credentials dans `.env`
3. Lancer l'app