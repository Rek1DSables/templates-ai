# 28 — Analyseur de Contrats AI

Pipeline d'analyse contractuelle automatisée. LangGraph orchestre 3 agents en séquence : extraction des clauses clés, identification des risques avec scoring, génération du résumé exécutif et recommandations. Upload PDF ou saisie texte directe. Export PDF inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — extraction clauses, analyse risques, recommandations
- **PyMuPDF** — extraction texte depuis PDF
- **FPDF2** — export PDF du rapport
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Upload PDF ou saisie texte directe
- 9 types de contrats supportés
- Extraction automatique de 10 clauses clés (parties, objet, durée, prix, PI, confidentialité, responsabilité, résiliation, litiges...)
- Analyse des risques avec niveau (critique / élevé / moyen / faible)
- Score de risque global 0-100
- Résumé exécutif avec verdict (signer / négocier / rejeter)
- Recommandations prioritaires avec nouvelles rédactions proposées
- Export PDF du rapport complet
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
28-analyseur-contrats/
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

Coller directement le texte d'un contrat de prestation avec des clauses déséquilibrées (responsabilité illimitée, PI cédée gratuitement, non-concurrence excessive).

## Notes

- Rapport complet : upgrade Sonnet prévu sur `generer_resume` en passe polish

## Modèle utilisé

`claude-haiku-4-5-20251001`