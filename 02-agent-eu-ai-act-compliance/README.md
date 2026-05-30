# 02 — EU AI Act Compliance Agent

AI compliance audit pipeline for EU AI Act (Regulation 2024/1689). 5 specialized agents: system classification, article-by-article analysis, remediation plan, final verdict. Complete timestamped audit trail compliant with Article 17 requirements.

## Stack

- **LangGraph** — sequential orchestration 5 agents
- **Anthropic Claude Sonnet** — remediation plan and verdict
- **Anthropic Claude Haiku** — classification and article analysis
- **FPDF2** — full PDF report export
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Classification | Risk level (Unacceptable / High / Limited / Minimal), critical flags detection |
| Article Analysis | Compliance per article (6, 9, 10, 13, 14, 15, 17, 72) with score and gaps |
| Remediation Part 1 | Executive summary, priority gaps per article |
| Remediation Part 2 | 90-day action plan, 15-point compliance checklist |
| Final Verdict | Go/No-Go, regulatory risk, 3 immediate actions |

## Features

- Automatic risk level classification with regulatory justification
- Detection of forbidden practices (Article 5)
- Compliance analysis per applicable article
- Critical flags detection (discrimination, fundamental rights, opacity, GPAI)
- Global compliance score 0-100
- 90-day remediation plan with owners and deadlines
- 15-point compliance checklist
- Complete timestamped audit trail (compliant with Article 17)
- Full PDF report + JSON audit trail export
- EU AI Act 2025-2027 deadline banner
- Retry automatic (3 attempts, 5s)

## Key Deadlines

| Date | Obligation |
|------|-----------|
| February 2025 | Prohibited practices (Article 5) — IN FORCE |
| August 2025 | GPAI obligations — IN FORCE |
| **August 2026** | **High-risk systems Annex III — DEADLINE** |
| August 2027 | Embedded systems in existing products |

## Structure

```
02-agent-eu-ai-act-compliance/
├── app.py          # Streamlit interface + audit trail
├── graph.py        # LangGraph 5 agents
├── config.py       # EU AI Act articles, risk levels, deadlines
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

## Test Data

- Name: RecrutAI Pro
- Sector: HR / Recruitment
- Category: Employment and workers management
- Data: CVs, LinkedIn profiles, biographical data, AI scores
- Description: Automatic CV scoring system for candidate pre-selection
- Expected result: HIGH risk level, 7 critical flags, score ~40-60/100

## Models

- `claude-haiku-4-5-20251001` — classification and article analysis
- `claude-sonnet-4-6` — remediation plan and verdict