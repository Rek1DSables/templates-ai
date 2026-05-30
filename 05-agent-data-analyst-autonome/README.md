# 05 — Autonomous Data Analyst Agent

Multi-agent data analysis pipeline in natural language. 4 specialized agents: question → SQL translation with auto-correction, execution and validation, insights analysis, executive commentary. Connected to SQLite in demo, PostgreSQL/Supabase/BigQuery in production.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — insights analysis and executive commentary
- **Anthropic Claude Haiku** — SQL generation and auto-correction
- **SQLite** — demo database (replaceable by PostgreSQL/Supabase)
- **Plotly** — automatic visualizations (bar, line, pie, scatter)
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Text-to-SQL | Translates question to valid SQL, chooses visualization type |
| Execution & Validation | Executes SQL, auto-corrects if error, retries |
| Insights Analysis | Analyzes results, detects trends and anomalies |
| Executive Commentary | 3-sentence synthesis for management |

## What Makes This Different From a Standard LLM

- **Connected to a real SQL database** — real figures, not hallucinated
- **Auto-correction** — if SQL fails, the agent corrects and retries
- **Automatic visualization** — chooses bar/line/pie/scatter based on the question
- **Audit trail** — every query timestamped
- **Production-ready** — connect PostgreSQL, Supabase or BigQuery in 2 lines

## Features

- Natural language questions on any SQL database
- SQL generation with explanation and recommended visualization type
- SQL auto-correction on execution error
- 8 pre-configured example questions
- Demo SQLite database included (sales + clients, 20 transactions)
- Automatic Plotly visualizations based on data type
- CSV results export
- Full JSON audit trail
- Retry automatic (3 attempts, 5s)

## Structure

```
05-agent-data-analyst-autonome/
├── app.py          # Streamlit interface + visualizations
├── graph.py        # LangGraph 4 agents + DB init
├── config.py       # Demo schema, example questions
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
DB_TYPE=sqlite
DB_URL=demo.db
```

## Connecting to Production Database

In `graph.py`, replace `sqlite3.connect(DB_URL)` with:
```python
# PostgreSQL
import psycopg2
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
```

## Test Questions

- What is the total revenue by region?
- Which are the top 5 best-selling products?
- Which sales rep has the best revenue?
- Identify customers at risk of churn

## Models

- `claude-haiku-4-5-20251001` — SQL generation and correction
- `claude-sonnet-4-6` — insights analysis and executive commentary