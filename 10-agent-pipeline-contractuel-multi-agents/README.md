# 10 — Contractual Pipeline Agent (Multi-Agent)

Multi-agent full contractual lifecycle pipeline. 4 specialized agents: clause extraction and structuring, legal risk analysis, synthesis with verdict, improved or new contract generation. 3 modes: analyze, generate, analyze + improve.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — synthesis and contract generation
- **Anthropic Claude Haiku** — clause extraction and risk analysis
- **Supabase** — processed contracts persistence
- **PyMuPDF** — text extraction from PDF
- **FPDF2** — full PDF report + contract export
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Extraction | Extracts and structures all contractual clauses |
| Risk Analysis | Identifies risks, abusive clauses, illegalities |
| Synthesis | Verdict, recommendations, actions before signature |
| Generation | Improved contract or new compliant contract |

## Features

- 3 modes: Analyze / Generate / Analyze + Improve
- 8 supported contract types
- Automatic detection of missing mandatory clauses
- Risk matrix by level (critical / high / medium / low)
- Global risk score 0-100
- Detection of abusive clauses and illegalities (payment terms > 60 days, unlimited liability)
- Automatically generated improved contract with identified risk corrections
- PDF upload or text input
- Demo document included with intentional abusive clauses
- Supabase persistence
- Full PDF report + JSON audit trail export
- Retry automatic (3 attempts, 5s)

## Structure

```
10-agent-pipeline-contractuel-multi-agents/
├── app.py          # Streamlit interface
├── graph.py        # LangGraph 4 agents
├── config.py       # Contract types, mandatory clauses
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

## Test Document

INNOVATECH-DEVPRO contract with 4 intentional anomalies:
- Payment term 90 days (illegal — max 60 days)
- Unlimited contractor liability
- Asymmetric termination (6 months contractor vs 0 client)
- Assignment of contractor's proprietary tools IP

## Models

- `claude-haiku-4-5-20251001` — extraction and risks
- `claude-sonnet-4-6` — synthesis and generation