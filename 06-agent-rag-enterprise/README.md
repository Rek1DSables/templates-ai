# 06 — Agent RAG Enterprise

Base de connaissance privée avec gouvernance par permissions, retrieval vectoriel, anti-hallucination et audit trail complet. 4 agents spécialisés : indexation avec chunking stratégique, retrieval avec filtrage permissions, génération ancrée dans les sources, vérification anti-hallucination.

## Stack

- **LangGraph** — orchestration 4 agents + routeur indexation/interrogation
- **Anthropic Claude Sonnet** — génération réponse ancrée dans les sources
- **Anthropic Claude Haiku** — vérification anti-hallucination
- **Sentence Transformers** — embeddings multilingues (paraphrase-multilingual-MiniLM-L12-v2)
- **Vector Store in-memory** — remplaçable par Pinecone/Weaviate/Qdrant en production
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Indexation | Chunking stratégique + embeddings + registre documents |
| Agent Retrieval & Gouvernance | Similarité cosinus + filtrage permissions par profil |
| Agent Génération | Réponse ancrée dans les sources avec citations [SOURCE N] |
| Agent Anti-Hallucination | Vérifie que la réponse ne contient pas de faits inventés |

## Fonctionnalités

- 4 niveaux de permission : public / interne / confidentiel / secret
- 7 profils utilisateur avec permissions configurables
- Chunks masqués automatiquement selon le profil connecté
- Citations de sources obligatoires dans chaque réponse
- Score de confiance basé sur la similarité vectorielle
- Détection d'hallucination — alerte si fait inventé absent des sources
- Audit trail complet horodaté (indexation + retrieval + génération)
- 4 documents de démo inclus (politique remboursement, tarifs, API, onboarding)
- Ajout de documents custom via interface
- Export audit trail JSON
- Retry automatique (3 tentatives, 5s)

## Ce qui différencie ce RAG d'un chatbot PDF basique

- **Gouvernance** — un employé ne voit pas les documents confidentiels
- **Anti-hallucination** — vérifie que la réponse est ancrée dans les sources
- **Audit trail** — chaque requête tracée pour conformité RGPD/ISO 27001
- **Production-ready** — remplacer le vector store in-memory par Pinecone/Weaviate en 10 lignes

## Structure

```
06-agent-rag-enterprise/
├── app.py          # Interface Streamlit + sidebar permissions
├── graph.py        # LangGraph 4 agents + vector store
├── config.py       # Permissions, chunks, modèles
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
```

## Migration vers vector store production

```python
# Pinecone
import pinecone
pinecone.init(api_key="...", environment="...")
index = pinecone.Index("rag-enterprise")
index.upsert([(chunk_id, embedding, metadata)])

# Weaviate
import weaviate
client = weaviate.Client("http://localhost:8080")
```

## Questions de test

- "Quelle est la politique de remboursement ?" (public — tous profils)
- "Quel est le prix de l'offre Enterprise ?" (confidentiel — Manager+)
- "Comment configurer les webhooks API ?" (interne — tous sauf public)
- "Quelles sont les étapes de l'onboarding ?" (interne — tous)

## Modèles utilisés

- `claude-haiku-4-5-20251001` — vérification anti-hallucination
- `claude-sonnet-4-6` — génération réponse
- `paraphrase-multilingual-MiniLM-L12-v2` — embeddings multilingues