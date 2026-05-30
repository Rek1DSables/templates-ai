# 01 — B2B Workflow Agent

Multi-agent pipeline for automated B2B email processing with full CRM integration. 5 specialized agents in sequence: CRM lookup, classification, CRM update, response generation, Gmail send.

## Stack

- **LangGraph** — sequential orchestration with conditional spam router
- **Anthropic Claude Sonnet** — contextualized response generation
- **Anthropic Claude Haiku** — classification and entity extraction
- **Supabase** — CRM (contacts, tickets, interactions)
- **Gmail API** — automatic reply sending
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| CRM Lookup | Searches contact, retrieves interaction history |
| Classification | Category, priority, sentiment, extracted entities |
| CRM Update | Creates ticket, updates contact, schedules follow-up |
| Response | Generates contextualized reply with ticket number |
| Gmail | Sends reply (real) or simulates (demo) |

## Features

- 8 classification categories (Support, Commercial, Complaint, Partnership, HR, Spam...)
- 4 priority levels with automatic SLA (2h / 8h / 24h / 72h)
- Automatic routing to the right team
- Unique ticket reference creation
- Automatic follow-up scheduling based on SLA
- Interaction history retrieved from Supabase
- Personalized response based on client segment and value
- Demo mode (4 test emails) or real Gmail
- Complete timestamped audit trail
- Audit trail JSON export

## Structure

```
01-agent-workflow-b2b/
├── app.py              # Streamlit interface
├── graph.py            # LangGraph 5 agents + router
├── config.py           # Configuration + SQL setup
├── requirements.txt
├── .env
├── credentials.json    # Gmail OAuth2 (not versioned)
├── token.json          # Gmail token (not versioned)
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
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## Supabase Setup

Run the SQL available in the interface (Setup tab) to create the 3 tables: crm_contacts, crm_tickets, crm_interactions.

## Gmail OAuth2

```powershell
copy path\to\credentials.json .
copy path\to\token.json .
```

## Test Data

4 demo emails included: technical urgency, commercial prospecting, formal complaint, spam.

## Models

- `claude-haiku-4-5-20251001` — classification and extraction
- `claude-sonnet-4-6` — response generation