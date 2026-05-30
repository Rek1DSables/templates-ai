# 04 — SDR / Revenue Agent

Multi-agent autonomous B2B prospecting pipeline. 4 specialized agents: web enrichment per prospect, ICP scoring, personalized 3-email sequence generation, Gmail first email send.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — personalized email sequence generation
- **Anthropic Claude Haiku** — ICP scoring and enrichment
- **Serper** — web search for business signals per prospect
- **Supabase** — prospects and sequences CRM
- **Gmail API** — sequence first email send
- **Plotly** — ICP score visualization
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Enrichment | Web search (Serper) + AI qualification + business signals |
| Scoring | ICP score 0-100, hot/warm/cold segmentation, Supabase save |
| Sequence | 3 personalized emails per prospect (hot + warm only) |
| Send | First email via Gmail (optional) |

## Features

- ICP configuration: target sectors, positions and company sizes
- Automatic web enrichment via Serper per prospect
- ICP scoring 0-100 with segmentation hot (75+) / warm (50-74) / cold (<50)
- Business signals detection (fundraising, hiring, news)
- 3-email sequence: first contact + follow-up D+5 + breakup D+12
- Ultra-personalized emails based on segment, signals and approach angle
- Automatic save of prospects and sequences in Supabase
- Demo mode (5 fictional prospects) or CSV upload
- Downloadable CSV template
- Qualified prospects CSV + complete pipeline JSON export
- Retry automatic (3 attempts, 5s)

## Structure

```
04-agent-sdr-revenue/
├── app.py              # Streamlit interface + visualizations
├── graph.py            # LangGraph 4 agents
├── config.py           # ICP, scoring, SQL setup
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
SERPER_API_KEY=your_serper_key
GMAIL_CREDENTIALS_FILE=credentials.json
GMAIL_TOKEN_FILE=token.json
```

## CSV Contact Format

```csv
nom,prenom,email,entreprise,poste,secteur,taille_entreprise,site_web
Martin,Sophie,sophie@acme.com,Acme Corp,CEO,SaaS B2B,PME,acme.com
```

## Models

- `claude-haiku-4-5-20251001` — ICP scoring and enrichment
- `claude-sonnet-4-6` — email sequence generation