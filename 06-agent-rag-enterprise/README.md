# 06 — Enterprise RAG Agent

Private knowledge base with permission governance, vector retrieval, anti-hallucination and complete audit trail. 4 specialized agents: strategic chunking indexation, permission-filtered retrieval, source-anchored generation, hallucination verification.

## Stack

- **LangGraph** — 4 agents + indexation/query router
- **Anthropic Claude Sonnet** — source-anchored response generation
- **Anthropic Claude Haiku** — anti-hallucination verification
- **Sentence Transformers** — multilingual embeddings (paraphrase-multilingual-MiniLM-L12-v2)
- **In-memory Vector Store** — replaceable by Pinecone/Weaviate/Qdrant in production
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Indexation | Strategic chunking + embeddings + document registry |
| Retrieval & Governance | Cosine similarity + permission filtering per profile |
| Generation | Source-anchored response with [SOURCE N] citations |
| Anti-Hallucination | Verifies response contains no invented facts |

## What Makes This Different From a Basic PDF Chatbot

- **Permission governance** — a standard employee doesn't see confidential documents
- **Anti-hallucination** — every fact verified against sources, alert if invention detected
- **Mandatory citations** — every claim sourced with [SOURCE N]
- **Audit trail** — every query timestamped for GDPR / ISO 27001 compliance

## Features

- 4 permission levels: public / internal / confidential / secret
- 7 user profiles with configurable permissions
- Chunks automatically masked based on connected profile
- Confidence score based on vector similarity
- Hallucination detection — alert if invented fact in sources
- Complete timestamped audit trail
- 4 demo documents included
- Custom document addition via interface
- JSON audit trail export
- Retry automatic (3 attempts, 5s)

## Structure

```
06-agent-rag-enterprise/
├── app.py          # Streamlit interface + permission sidebar
├── graph.py        # LangGraph 4 agents + vector store
├── config.py       # Permissions, chunks, models
├── requirements.txt
├── .env
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Environment Variables

```
ANTHROPIC_API_KEY=your_key
```

## Migrating to Production Vector Store

```python
# Pinecone
import pinecone
pinecone.init(api_key="...", environment="...")
index = pinecone.Index("rag-enterprise")
index.upsert([(chunk_id, embedding, metadata)])
```

## Test Questions

- "What is the refund policy?" (public — all profiles)
- "What is the price of the Enterprise plan?" (confidential — Manager+)
- "How to configure API webhooks?" (internal — all)
- "What are the onboarding steps?" (internal — all)

## Models

- `claude-haiku-4-5-20251001` — anti-hallucination verification
- `claude-sonnet-4-6` — response generation
- `paraphrase-multilingual-MiniLM-L12-v2` — multilingual embeddings