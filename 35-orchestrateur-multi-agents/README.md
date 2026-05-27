# 35 — Orchestrateur Multi-Agents AI

Agent orchestrateur qui décompose automatiquement une tâche complexe en sous-tâches et dispatche vers des agents spécialisés en séquence. LangGraph orchestre 3 nœuds : orchestration (décomposition JSON), dispatcher (exécution des agents), agrégateur (synthèse finale). Export PDF du rapport inclus.

## Stack

- **LangGraph** — orchestration des 3 nœuds
- **Anthropic Claude** — orchestrateur + 4 agents spécialisés (recherche, analyse, rédaction, synthèse)
- **Serper** — recherche web pour l'agent recherche
- **FPDF2** — export PDF du rapport final
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Décomposition automatique de la tâche en sous-tâches via JSON structuré
- 4 agents spécialisés : recherche web, analyse, rédaction, synthèse
- Contexte cumulatif transmis entre agents (chaque agent bénéficie des résultats précédents)
- Livrable finale agrégée et structurée
- Export PDF téléchargeable
- Détail des résultats par agent dans un onglet dédié
- 4 exemples de tâches préconfigurés
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
35-orchestrateur-multi-agents/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph orchestrateur + dispatcher + agregateur
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

- Tache : Analyse le marche de l'IA generative en Europe en 2025 et redige un rapport executif

## Modèle utilisé

`claude-haiku-4-5-20251001`