# 12 — SI Integration & Webhook Agent

Multi-agent information system integration pipeline via events. 4 specialized agents: reception and idempotent validation, transformation and multi-destination mapping, retry send with dead letter queue, integration report.

## Stack

- **LangGraph** — orchestration 4 agents + conditional router
- **Anthropic Claude Sonnet** — report and recommendations
- **Anthropic Claude Haiku** — payload validation and mapping
- **Supabase** — events and dead letter queue persistence
- **Requests** — HTTP send to real destinations
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Reception & Validation | SHA-256 deduplication, AI payload validation |
| Transformation & Mapping | Format adaptation per destination, enrichments |
| Send & Retry | Configurable retry, automatic dead letter |
| Report | Integration metrics, recommendations |

## Implemented Patterns

- **Idempotency** — SHA-256 event_id to avoid duplicates
- **Retry** — 3 strategies: exponential / linear / fixed
- **Dead Letter Queue** — Supabase persistence of failed events
- **Conditional router** — invalid payload → direct dead letter
- **Multi-destination** — one payload → N target systems

## Features

- 5 integration types: webhook, polling, event-driven, ETL, bidirectional sync
- 7 target systems: CRM, ERP, Slack, DB, Email, Webhook, REST API
- 4 demo payloads: Stripe payment, GitHub PR, CRM lead, monitoring alert
- AI payload validation with quality score
- Transformation and mapping adapted per destination
- Configurable exponential backoff retry
- Dead Letter Queue with error detail and payload
- Demo mode (simulated sends) or real (HTTP)
- JSON audit trail + full report export
- Retry automatic (3 attempts, 5s)

## Structure

```
12-agent-integration-si-webhook/
├── app.py          # Streamlit interface
├── graph.py        # LangGraph 4 agents + router
├── config.py       # Types, retry strategies, demo payloads
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
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Quick Test

Demo mode → Payload "Stripe Payment Webhook" → CRM + Database → Launch

## Models

- `claude-haiku-4-5-20251001` — validation and mapping
- `claude-sonnet-4-6` — report and recommendations