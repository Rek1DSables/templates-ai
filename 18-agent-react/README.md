# 33 — Agent de Recherche Autonome ReAct

Agent de recherche autonome basé sur le pattern ReAct (Reasoning + Acting). L'agent raisonne en boucle, lance des recherches web Serper à chaque étape, observe les résultats et itère jusqu'à construire une réponse complète. Traduction automatique en français en sortie.

## Stack

- **LangGraph** — orchestration de la boucle ReAct
- **Anthropic Claude** — raisonnement et synthèse
- **Serper** — recherche web en temps réel
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Boucle ReAct : Pensée → Action → Observation → itération
- Recherche web automatique à chaque étape (Serper)
- Maximum 5 iterations configurables
- Traduction automatique de la réponse finale en français
- Raisonnement détaillé visible dans un onglet dédié (pensées, actions, observations)
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
33-agent-react/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph ReAct + traduction
├── config.py       # Configuration centralisee
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
SERPER_API_KEY=ta_clé_serper
```

## Données de test

- Question : Quelles sont les differences entre LangGraph et CrewAI pour un projet de production en 2025 ?

## Modèle utilisé

`claude-haiku-4-5-20251001`