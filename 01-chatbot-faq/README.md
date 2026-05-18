# 💬 01 — Chatbot FAQ intelligent

Agent RAG qui répond aux questions d'une base de connaissance PDF via une interface Streamlit.

## Fonctionnement

1. Dépose tes PDFs dans le dossier `docs/`
2. L'agent vectorise les documents automatiquement
3. L'utilisateur pose ses questions en langage naturel
4. L'agent retrouve les passages pertinents et génère une réponse

## Stack technique

- **LangGraph** — orchestration du pipeline RAG
- **FAISS** — index vectoriel local
- **BAAI/bge-m3** — modèle d'embeddings multilingue
- **Anthropic Claude Haiku** — génération des réponses
- **Streamlit** — interface utilisateur

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Tout se passe dans `config.py` :
- `APP_TITLE` — nom affiché dans l'interface
- `DOCS_FOLDER` — dossier des PDFs (défaut : `docs/`)
- `TOP_K` — nombre de chunks retournés
- `CHUNK_SIZE` — taille des chunks
- `EMBEDDING_MODEL` — modèle d'embeddings
- `MODEL` — modèle Anthropic utilisé

## Lancement

```bash
streamlit run app.py
```

## Adaptation client

Pour adapter ce template à un nouveau client :
1. Modifier `config.py` selon les besoins
2. Déposer les PDFs du client dans `docs/`
3. Lancer l'app

## Variables d'environnement

Créer un fichier `.env` :
```
ANTHROPIC_API_KEY=ta_clé_ici
```