# 11 — LLM Quality Evaluation Agent

Multi-agent LLM quality evaluation pipeline before deployment. 4 specialized agents: test case execution, multi-dimension scoring, regression detection, deployability report with quality badge.

## Stack

- **LangGraph** — sequential orchestration 4 agents
- **Anthropic Claude Sonnet** — report and recommendations
- **Anthropic Claude Haiku** — evaluation and scoring
- **Plotly** — radar chart of dimension scores
- **Streamlit** — user interface

## Agents

| Agent | Role |
|-------|------|
| Execution | Executes each test case on the evaluated model |
| Evaluation | Scores each response on 7 quality dimensions |
| Regression | Detects hallucinations, toxicity, failed critical tests |
| Report | Deployability report with quality badge |

## Features

- 7 evaluation dimensions: faithfulness, completeness, accuracy, hallucination, relevance, coherence, toxicity
- 6 test types: unit, regression, adversarial, robustness, load, business
- Automatic quality badge: 🟢 Production Ready / 🟡 Staging Only / 🟠 Dev Only / 🔴 Not Deployable
- Blocking regression detection (hallucination, toxicity, failed critical tests, excessive latency)
- Dimension score radar chart
- Deployability report with Go / No-Go verdict
- 5 demo test cases included (unit, adversarial, business, robustness)
- Compatible with all models: Anthropic, OpenAI, DeepSeek, Mistral
- Full JSON report + CSV results export
- Retry automatic (3 attempts, 5s)

## Use Cases

- Validate an AI agent before production deployment
- Compare two versions of a model or prompt
- Detect regressions after update
- Produce a formal report for CTO / CISO validation

## Structure

```
11-agent-evaluation-qualite-llm/
├── app.py          # Streamlit interface + radar chart
├── graph.py        # LangGraph 4 agents
├── config.py       # Dimensions, thresholds, demo test cases
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

## Quick Test

Select "Demo cases" + model `claude-haiku-4-5-20251001` + click Launch.

## Models

- `claude-haiku-4-5-20251001` — evaluation and scoring
- `claude-sonnet-4-6` — report and recommendations