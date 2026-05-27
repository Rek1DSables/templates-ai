# 27 — Agent de Support Technique AI

Pipeline de support technique automatisé. LangGraph orchestre 3 agents en séquence : diagnostic de la cause racine, génération de 3 solutions priorisées avec code, plan de résolution étape par étape avec checklist et prévention future.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — diagnostic, solutions, plan de résolution
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 10 technologies supportées (Python, JS, Docker, AWS, PostgreSQL, LangGraph...)
- 6 types de problèmes (erreur, performance, bug logique, déploiement, sécurité...)
- 4 niveaux d'urgence avec code couleur
- Diagnostic : cause racine, facteurs aggravants, impact, complexité, temps estimé
- 3 solutions priorisées : fix immédiat, solution complète, alternative
- Plan de résolution étape par étape avec code exact
- Checklist de vérification et recommandations de prévention
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
27-agent-support-technique/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph 3 agents
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
```

## Données de test

- Technologie : Python
- Type : Erreur / Exception
- Urgence : Haute (impact utilisateurs)
- Description : Mon agent LangGraph plante avec une erreur RecursionError apres 5 iterations. Le graph tourne en boucle infinie malgre ma condition de sortie.
- Logs : RecursionError: maximum recursion depth exceeded at node: agent_node iteration 47

## Modèle utilisé

`claude-haiku-4-5-20251001`