# 07 — Advanced Document Analysis Agent

Multi-agent pipeline for complex legal and financial document analysis. 4 specialized agents in sequence: structured extraction per axis, risk verification, executive synthesis, risk matrix and recommendations. Full PDF export with audit trail.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — synthesis and recommendations
- **Anthropic Claude Haiku** — structured extraction and risk identification
- **PyMuPDF** — text extraction from uploaded PDF
- **FPDF2** — full PDF report export
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Extraction | Extracts data for each analysis axis |
| Risk Verification | Identifies risks, inconsistencies, missing critical elements |
| Synthesis Part 1 | Executive summary + extracted information |
| Synthesis Part 2 | Risk matrix + recommendations + verdict |

## Features

- 10 document types: commercial contract, lease, RFP, due diligence, NDA, T&Cs, audit, employment contract, partnership
- Analysis axes configured per document type (8-9 axes per type)
- Structured extraction with reliability score and document location
- Risk matrix by level (critical / high / medium / low)
- Global risk score 0-100
- Verdict: sign / negotiate / do not sign
- 5 priority recommendations with owner and deadline
- PDF upload or text input
- Demo document included (commercial contract with abusive clauses)
- Full PDF report + JSON audit trail export
- Retry automatic (3 attempts, 5s)

## What Makes This Different From a Simple LLM Prompt

- **Multi-agent pipeline** — extraction → verification → synthesis in sequence
- **Axes configured per type** — not a generic prompt but structured business analysis
- **Abusive clause detection** — illegal payment terms, unlimited liability, asymmetric termination
- **Audit trail** — every extraction traceable with reliability score

## Structure

```
07-agent-analyse-documentaire/
├── app.py          # Streamlit interface + PDF export
├── graph.py        # LangGraph 4 agents
├── config.py       # Document types, analysis axes
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

## Test Document

Commercial contract TECHCORP-DEVAGENCY with 4 intentional abusive clauses:
- Illegal payment term (90 days vs 60 days legal max)
- Unlimited contractor liability
- Asymmetric termination (Client: no notice, Contractor: 6 months)
- Assignment of generic proprietary tools intellectual property

## Models

- `claude-haiku-4-5-20251001` — structured extraction and risks
- `claude-sonnet-4-6` — synthesis and recommendations