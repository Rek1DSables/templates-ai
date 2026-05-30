# 09 — Monitoring & Alerts Agent

Real-time multi-agent monitoring pipeline. 4 specialized agents: threshold violation detection, causal analysis and correlations, graduated alert generation, report and Gmail notification. Health score dashboard with Plotly gauge.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — report and causal analysis
- **Anthropic Claude Haiku** — violation detection and alert generation
- **Supabase** — alert and metrics persistence
- **Plotly** — health gauge + visualizations
- **Gmail API** — email notification if critical alerts
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Detection | Compares metrics vs thresholds, calculates deviations and levels |
| Causal Analysis | Correlations, root cause, global health score 0-100 |
| Alert Generation | Structured alert per violation, Supabase save |
| Report & Notification | Synthetic report + optional Gmail send |

## Features

- 8 pre-configured metrics (API, conversion, churn, CPU, memory, revenue, tickets)
- 4 alert levels: critical (SLA 15min) / high (60min) / medium (4h) / info (24h)
- Global health score 0-100 with Plotly gauge
- Causal analysis and correlations between violations
- Recommended actions with owner and deadline
- Alert persistence in Supabase
- Critical alert Gmail notification
- Demo mode (8 metrics with violations) or manual configuration
- Alerts CSV + full JSON report export
- Retry automatic (3 attempts, 5s)

## Structure

```
09-agent-monitoring-alertes/
├── app.py              # Streamlit interface + gauge
├── graph.py            # LangGraph 4 agents
├── config.py           # Thresholds, alert levels, SQL
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

## Test Data

Demo mode activated by default — 8 metrics with intentional violations:
- error_rate_api: 12.5% (threshold 5%)
- response_time_ms: 3200ms (threshold 2000ms)
- conversion_rate: 1.2% (threshold 2%)
- monthly_churn: 8.5% (threshold 5%)
- cpu_usage: 92% (threshold 85%)
- daily_revenue: €450 (threshold €1000)
- open_tickets: 35 (threshold 20)

## Models

- `claude-haiku-4-5-20251001` — detection and alerts
- `claude-sonnet-4-6` — causal analysis and report