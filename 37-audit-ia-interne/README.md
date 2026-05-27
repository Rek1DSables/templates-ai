# 37 — Système d'Audit IA Interne

Pipeline d'audit IA qui analyse les processus d'une entreprise, identifie les opportunités d'automatisation chiffrées et génère un roadmap d'implémentation priorisé par ROI. Export PDF du rapport inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — analyse processus, identification opportunités, génération roadmap
- **FPDF2** — export PDF du rapport d'audit
- **Streamlit** — interface consultant

## Fonctionnalités

- Formulaire entreprise (nom, secteur, taille, budget IA, description processus)
- Agent 1 : cartographie et analyse de maturité digitale
- Agent 2 : identification de 4 à 6 opportunités d'automatisation avec scoring ROI (JSON structuré)
- Agent 3 : roadmap en 3 phases (Quick Wins, Consolidation, Transformation)
- Score global d'automatisabilité calculé automatiquement
- Opportunités détaillées : gain temps, ROI estimé, complexité, technologie recommandée
- Export PDF du rapport complet
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
37-audit-ia-interne/
├── app.py          # Interface Streamlit + export PDF
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

- Entreprise : Acme Corp
- Secteur : E-commerce
- Taille : 10-50 employes
- Budget : 5 000 - 20 000 EUR
- Processus : traitement commandes manuel, support 50 tickets/jour, facturation Word, reporting 4h/semaine

## Notes

- Le noeud `generer_roadmap` gagne en qualite avec claude-sonnet (a activer en production)
- Polish global prevu : upgrade Sonnet sur ce noeud uniquement

## Modèle utilisé

`claude-haiku-4-5-20251001`