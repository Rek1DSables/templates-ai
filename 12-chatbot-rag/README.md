# 12 — Chatbot RAG sur Documentation Technique

Chatbot intelligent basé sur vos documents : upload d'un PDF → indexation automatique → questions/réponses en langage naturel.

**Stack :** LangGraph · FAISS · HuggingFace · PyMuPDF · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
load_document → retrieve_context → generate_answer
```

---

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Variables d'environnement (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Fonctionnement

1. Uploadez un PDF dans le panneau gauche
2. Le document est découpé en chunks et indexé dans FAISS
3. À chaque question, les chunks les plus pertinents sont récupérés
4. Le LLM génère une réponse basée uniquement sur le contenu du document

---

## Différence avec le Chatbot FAQ (01)

| FAQ | RAG |
|---|---|
| Base de réponses fixe | N'importe quel PDF |
| Préparation manuelle | Aucune préparation |
| Idéal site vitrine | Idéal documentation technique |

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `CHUNK_SIZE` | Taille des chunks en caractères (défaut : 500) |
| `CHUNK_OVERLAP` | Chevauchement entre chunks (défaut : 50) |
| `TOP_K` | Nombre de chunks retournés (défaut : 3) |
| `CHATBOT_NAME` | Nom affiché dans l'interface |
| `WELCOME_MESSAGE` | Message d'accueil |