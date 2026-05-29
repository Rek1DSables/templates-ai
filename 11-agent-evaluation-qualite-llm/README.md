# 11 — Agent Évaluation Qualité LLM

Pipeline multi-agents d'évaluation de la qualité des LLM avant déploiement. 4 agents spécialisés : exécution des cas de test, scoring multi-dimensions, détection des régressions, rapport de déployabilité avec badge qualité.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — rapport et recommandations
- **Anthropic Claude Haiku** — évaluation et scoring
- **Plotly** — radar chart des scores par dimension
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Exécution | Exécute chaque cas de test sur le modèle évalué |
| Agent Évaluation | Score chaque réponse sur 7 dimensions de qualité |
| Agent Régression | Détecte hallucinations, toxicité, tests critiques échoués |
| Agent Rapport | Rapport déployabilité avec badge qualité |

## Fonctionnalités

- 7 dimensions d'évaluation : fidélité, complétude, précision, hallucination, pertinence, cohérence, toxicité
- 6 types de tests : unitaire, régression, adversarial, robustesse, charge, métier
- Badge qualité automatique : 🟢 Production Ready / 🟡 Staging Only / 🟠 Dev Only / 🔴 Non déployable
- Détection régressions bloquantes (hallucination, toxicité, tests critiques échoués, latence excessive)
- Radar chart des scores par dimension
- Rapport de déployabilité avec verdict Go / No-Go
- 5 cas de test de démo inclus (unitaire, adversarial, métier, robustesse)
- Compatible tous modèles Anthropic, OpenAI, DeepSeek, Mistral
- Export rapport JSON + résultats CSV
- Retry automatique (3 tentatives, 5s)

## Cas d'usage

- Valider un agent IA avant déploiement en production
- Comparer deux versions d'un modèle ou d'un prompt
- Détecter les régressions après mise à jour
- Produire un rapport formel pour validation DSI / RSSI

## Structure

```
11-agent-evaluation-qualite-llm/
├── app.py          # Interface Streamlit + radar chart
├── graph.py        # LangGraph 4 agents
├── config.py       # Dimensions, seuils, cas de test démo
├── requirements.txt
├── .env
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Variables d'environnement

```
ANTHROPIC_API_KEY=ta_clé_ici
```

## Test rapide

Sélectionner "Cas de démo" + modèle `claude-haiku-4-5-20251001` + cliquer Lancer.

## Modèles utilisés

- `claude-haiku-4-5-20251001` — évaluation et scoring
- `claude-sonnet-4-6` — rapport et recommandations