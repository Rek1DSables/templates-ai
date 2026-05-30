# 08 — M&A Due Diligence Agent

Multi-agent due diligence analysis pipeline for M&A, investment and partnership operations. 6 specialized agents: axis analysis, executive synthesis, detailed analysis, risk matrix, pre-closing conditions, final verdict with valuation range.

## Stack

- **LangGraph** — sequential orchestration 6 agents
- **Anthropic Claude Sonnet** — synthesis, recommendations, verdict
- **Anthropic Claude Haiku** — structural analysis per axis
- **FPDF2** — full PDF report export
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Axis Analysis | Evaluates each selected axis: score, positives, negatives, risks, key questions |
| Executive Synthesis | Go/No-Go/Conditional Go verdict, 5 key points, confidence score |
| Detailed Analysis | Synthesis per axis with strengths and watchpoints |
| Risk Matrix | Risk ranking by level with impact and mitigation plan |
| Pre-closing Conditions | Suspensive conditions, valuation adjustments, seller warranties |
| Final Verdict | Valuation range (low/recommended/high), 5 next steps, blocking points |

## Features

- 5 due diligence types: M&A, VC/PE Investment, Strategic Partnership, Supplier, Commercial Real Estate
- 7 configurable analysis axes: Financial, Legal, Commercial, Operational, Technology, HR, Risks
- Global score 0-100 per axis and overall
- Risk matrix (critical / high / medium / low)
- Suspensive conditions and warranties auto-generated
- Valuation range with 3 scenarios
- Go / No-Go / Conditional Go verdict with justification
- 5 next steps with owner and deadline
- Full PDF report export
- Retry automatic (3 attempts, 5s)

## Structure

```
08-agent-due-diligence/
├── app.py          # Streamlit interface
├── graph.py        # LangGraph 6 agents
├── config.py       # DD types, analysis axes
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

- Target: TechFlow SAS
- Type: M&A Due Diligence
- Sector: B2B SaaS
- Axes: Financial, Legal, Commercial
- Context: Acquisition considered at €3M, MRR €85k, 60% YoY growth
- Expected result: Conditional Go, valuation range €1.8M-€3M

## Models

- `claude-haiku-4-5-20251001` — structural analysis per axis
- `claude-sonnet-4-6` — synthesis, recommendations, verdict