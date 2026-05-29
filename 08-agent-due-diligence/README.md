# 11 — Agent Due Diligence

Pipeline d'analyse de due diligence multi-axes. LangGraph orchestre 6 nœuds : analyse par axe, synthèse executive, analyse détaillée, matrice des risques, conditions avant closing, verdict final. Rapport PDF complet.

## Stack

- **LangGraph** — orchestration séquentielle 6 nœuds
- **Anthropic Claude Sonnet** — analyse, synthèse et recommandations
- **FPDF2** — export PDF rapport complet
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 5 types de due diligence : M&A, Investissement VC/PE, Partenariat, Fournisseur, Immobilier
- 7 axes d'analyse configurables : Financier, Juridique, Commercial, Opérationnel, Technologique, RH, Risques
- Score global 0-100 par axe et global
- Matrice des risques (critique / élevé / moyen / faible)
- Conditions suspensives et garanties à obtenir
- Fourchette de valorisation avec 3 scénarios
- Verdict Go / No-Go / Go conditionnel avec justification
- 5 prochaines étapes avec responsable et délai
- Export PDF rapport complet
- Retry automatique (3 tentatives, 5s)

## Structure

```
11-agent-due-diligence/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph 6 nœuds
├── config.py       # Configuration centralisée
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

- Cible : TechFlow SAS
- Type : Due Diligence M&A
- Secteur : SaaS B2B
- Axes : Financier, Juridique, Commercial
- Contexte : Acquisition envisagée pour 3M€, MRR 85k€, croissance 60% YoY

## Modèles utilisés

- `claude-haiku-4-5-20251001` — analyse structurelle par axe
- `claude-sonnet-4-6` — synthèse, recommandations, verdict