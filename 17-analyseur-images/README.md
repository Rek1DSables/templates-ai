# 32 — Analyseur d'Images & Documents Visuels AI

Pipeline d'analyse visuelle par Claude Vision. L'utilisateur uploade une image et LangGraph orchestre 3 agents en séquence : description détaillée du contenu, extraction des données structurées, génération d'insights et recommandations actionnables.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude Vision** — analyse visuelle multimodale
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Upload d'image (jpg, jpeg, png, gif, webp, max 5MB)
- Aperçu de l'image avant analyse
- Description complète du contenu visuel (nature, éléments, contexte)
- Extraction des données structurées (textes, montants, dates, tableaux)
- Insights et recommandations actionnables
- Résultats affichés en 3 onglets
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
32-analyseur-images/
├── app.py          # Interface Streamlit + encodage base64
├── graph.py        # LangGraph 3 noeuds Vision
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

N'importe quelle image : facture, screenshot d'interface, schéma technique, photo de document, graphique. Le pipeline s'adapte automatiquement au type de contenu visuel détecté.

## Modèle utilisé

`claude-haiku-4-5-20251001`