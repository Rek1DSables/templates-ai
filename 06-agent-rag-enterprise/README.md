# 19 — Système RAG Multi-Sources

Chatbot RAG qui interroge simultanément plusieurs sources de données : PDFs, base Supabase, APIs externes — et cite ses sources pour chaque réponse.

**Stack :** LangGraph · FAISS · HuggingFace · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
retrieve_pdf_context → retrieve_supabase_context → retrieve_api_context
→ combine_contexts → generate_answer
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
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## Sources supportées

| Source | Configuration |
|---|---|
| PDFs | Upload direct dans la sidebar |
| Supabase | Nom de la table + colonnes |
| API externe | URL + clé API optionnelle |

---

## Différence avec le Chatbot RAG (12)

| RAG simple (12) | RAG Multi-Sources (19) |
|---|---|
| 1 PDF à la fois | Plusieurs PDFs simultanément |
| Source unique | PDF + Supabase + API |
| Pas de citation | Cite la source pour chaque info |

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `CHUNK_SIZE` | Taille des chunks PDF (défaut : 500) |
| `TOP_K` | Chunks retournés par source (défaut : 4) |
| `CHATBOT_NAME` | Nom affiché dans l'interface |