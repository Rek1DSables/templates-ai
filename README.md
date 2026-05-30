# AI Automation Templates — Enterprise Portfolio

A collection of 12 production-ready AI agents built with LangGraph and Claude API, targeting high-value business use cases with low competition from no-code tools or generic SaaS solutions.

Each template is standalone, documented, and deployable in under an hour.

---

## Why This Collection

These templates target the 3 levels that define enterprise-grade AI automation:

- **Vertical AI Agents** — encoded business logic, regulated domains, high technical barrier
- **Multi-Agent Architectures** — LangGraph orchestration, shared state, conditional routing
- **Enterprise Governance** — timestamped audit trails, permissions, regulatory compliance

What SaaS and no-code tools don't do: deep SI integration, audit trails for compliance, custom business logic, sensitive data governance.

---

## Templates

| # | Name | Use Case | Level |
|---|------|----------|-------|
| 01 | B2B Workflow Agent | Email → CRM lookup → Classification → Ticket → Reply → Gmail | 🔴 Expert |
| 02 | EU AI Act Compliance Agent | AI compliance audit — classification, gaps, remediation plan, audit trail | 🔴 Expert |
| 03 | Finance Close Agent | Multi-agent financial close — reconciliation, variances, journal entries, disclosure | 🔴 Expert |
| 04 | SDR / Revenue Agent | Enrichment → ICP Scoring → 3-email sequence → Gmail send | 🔴 Expert |
| 05 | Autonomous Data Analyst Agent | Natural language → SQL → Execution → Insights → Executive summary | 🔴 Expert |
| 06 | Enterprise RAG Agent | Private knowledge base with governance, permissions, anti-hallucination, audit trail | 🔴 Expert |
| 07 | Advanced Document Analysis Agent | Structured extraction → Risk verification → Synthesis → Risk matrix → PDF | 🔴 Expert |
| 08 | M&A Due Diligence Agent | Multi-axis analysis → Scoring → Risk matrix → Verdict → Valuation range | 🔴 Expert |
| 09 | Monitoring & Alerts Agent | Violation detection → Causal analysis → Graduated alerts → Gmail → Supabase | 🔴 Expert |
| 10 | Contractual Pipeline Agent | Clause extraction → Risk analysis → Synthesis → Improved contract generation | 🔴 Expert |
| 11 | LLM Quality Evaluation Agent | Tests → 7-dimension scoring → Regression detection → Deployability badge → Report | 🔴 Expert |
| 12 | SI Integration & Webhook Agent | Reception → Validation → Mapping → Retry → Dead Letter → Multi-destination | 🔴 Expert |

---

## Tech Stack

- **Orchestration** : LangGraph (multi-agents, conditional routers, loops)
- **LLM** : Anthropic Claude Haiku + Sonnet depending on the node
- **Interface** : Streamlit
- **Database** : Supabase (PostgreSQL)
- **Email** : Gmail API (OAuth2)
- **Web search** : Serper
- **Embeddings** : Sentence Transformers (multilingual)
- **Data** : Pandas, Plotly
- **PDF** : FPDF2, PyMuPDF
- **HTTP** : Requests (webhooks, third-party APIs)

---

## LLM Architecture

Each template uses two models depending on the node type:

- **claude-haiku-4-5-20251001** — extraction, classification, validation, JSON, structured analysis
- **claude-sonnet-4-6** — long-form generation, reports, recommendations, synthesis

---

## Switching LLM Provider

Default: Anthropic Claude (GDPR compliant, EU servers).

| Provider | Model | Cost vs Claude | Notes |
|----------|-------|----------------|-------|
| Anthropic (default) | claude-haiku-4-5 | reference | GDPR, EU servers |
| DeepSeek | deepseek-chat | ~10x cheaper | China servers |
| Mistral | mistral-small | ~3x cheaper | EU servers, GDPR |
| OpenAI | gpt-4o-mini | ~2x cheaper | US servers |

**Migration in 3 steps:**

```bash
pip install openai
```

In `config.py`:
```python
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "sk-..."
```

In `graph.py`:
```python
from openai import OpenAI
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
```

---

## API Cost Estimates

Monthly estimates with Anthropic Claude Haiku + Sonnet (default provider):

| Template | Light usage | Medium usage | Heavy usage |
|----------|-------------|--------------|-------------|
| 01 — B2B Workflow | Low | Medium | High |
| 02 — EU AI Act | Low | Medium | High |
| 03 — Finance Close | Low | Medium | High |
| 04 — SDR Revenue | Low | Medium | High |
| 05 — Data Analyst | Very low | Low | Medium |
| 06 — RAG Enterprise | Low | Medium | High |
| 07 — Document Analysis | Low | Medium | High |
| 08 — Due Diligence | Low | Medium | High |
| 09 — Monitoring | Very low | Low | Medium |
| 10 — Contractual Pipeline | Low | Medium | High |
| 11 — LLM Evaluation | Very low | Low | Medium |
| 12 — SI Integration | Very low | Low | Medium |

*Light: a few uses/day. Medium: regular team usage. Heavy: high-volume production.*

With DeepSeek: divide by 8 to 10. With Mistral Small: divide by 3.

---

## Typical Client Pipelines

**Full B2B commercial pipeline**
```
04 — SDR Revenue → 01 — B2B Workflow → 10 — Contractual Pipeline
```
Prospect enrichment → lead qualification → email handling → contract generation

---

**AI compliance pipeline (August 2026 deadline)**
```
02 — EU AI Act Compliance → 11 — LLM Quality Evaluation
```
Audit AI systems → validate quality before deployment

---

**M&A / investment pipeline**
```
07 — Document Analysis → 08 — Due Diligence → 10 — Contractual Pipeline
```
Analyze documents → due diligence → generate agreements

---

**Enterprise finance pipeline**
```
05 — Data Analyst → 03 — Finance Close → 09 — Monitoring
```
Analyze data → close books → monitor continuously

---

**SI & data pipeline**
```
12 — SI Integration → 06 — RAG Enterprise → 05 — Data Analyst
```
Ingest events → enrich knowledge base → analyze

---

## Cloud Deployment

**Streamlit Cloud (free)**
```bash
# Connect on share.streamlit.io
# Secrets: ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

**Railway**
```bash
# Procfile: web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
# Remove pywin32 from requirements.txt before Linux deployment
```

**Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

---

## Installation

```bash
cd XX-template-name
pip install -r requirements.txt
streamlit run app.py
```

Each template includes a `.env` file to configure and a `README.md` with complete instructions and test data.

---

## Requirements

- Python 3.10+
- Anthropic API key
- Supabase account (templates with persistence)
- Gmail account + OAuth2 credentials (email templates)
- Serper API key (SDR template with web enrichment)

---

## Available for Missions

AI Automation freelance consultant specializing in the design and deployment of custom AI agents for enterprise clients.

**Available on Malt and Upwork** for AI agent development missions, business process automation and Claude API integrations.

Stack: LangGraph · Claude API · MCP Protocol · Supabase · Streamlit · Multi-agent architectures

---

*Actively maintained collection.*