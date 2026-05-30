# 03 — Finance Close Agent

Multi-agent financial close pipeline. LangGraph orchestrates 7 specialized nodes: account reconciliation, Budget vs Actual variance analysis, closing journal entries generation, narrative report in 4 parts, complete audit log. PDF and JSON export.

## Stack

- **LangGraph** — sequential orchestration 7 nodes
- **Anthropic Claude Sonnet** — narrative report and disclosure
- **Anthropic Claude Haiku** — reconciliation, variances, journal entries
- **Plotly** — variance visualization
- **FPDF2** — full PDF report export
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Reconciliation | GL vs subsidiary balance discrepancy detection, anomalies, duplicates |
| Variance | Budget vs Actual analysis, performance scoring |
| Journal Entries | Balanced closing entries generation with auto-reverse flag |
| Disclosure ×4 | Narrative report, checklist, conclusion, validation |

## Features

- Demo mode (pre-filled Acme Corp data) or manual input
- Automatic multi-account reconciliation with anomaly detection
- Budget vs Actual variance analysis with configurable thresholds (critical >5%, high >2%)
- Balanced closing entries generation with auto-reverse flag
- Complete narrative report in 4 sections
- 8-point closing checklist
- Global quality score 0-100
- Timestamped audit log of all agent decisions
- PDF report + complete JSON data export
- Retry automatic (3 attempts, 5s)

## Supported Standards

IFRS, French GAAP (PCG), US GAAP

## Structure

```
03-agent-finance-close/
├── app.py          # Streamlit interface + visualizations
├── graph.py        # LangGraph 7 nodes
├── config.py       # Centralized configuration
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

Demo mode activated by default — Acme Corp SAS / May 2026 / IFRS / EUR

## Models

- `claude-haiku-4-5-20251001` — reconciliation, variances, journal entries
- `claude-sonnet-4-6` — narrative report and conclusion