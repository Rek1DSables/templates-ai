# 05 — Agent Analyse de Données

Pipeline d'analyse de données business. LangGraph orchestre 3 nœuds : analyse statistique de la structure, génération d'insights IA, complétion des recommandations. Visualisations automatiques Plotly, export PDF et CSV.

## Stack

- **LangGraph** — orchestration séquentielle
- **Anthropic Claude Sonnet** — insights et recommandations business
- **Pandas** — traitement et analyse des données
- **Plotly** — visualisations automatiques (scatter, histogram, bar, heatmap)
- **FPDF2** — export PDF du rapport
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Upload CSV ou Excel (xlsx, xls)
- 6 types d'analyse : exploratoire, anomalies, tendances, segmentation, performance commerciale, financière
- Analyse statistique automatique (types, valeurs manquantes, qualité des données)
- 4 visualisations automatiques selon les colonnes disponibles
- Insights détaillés + recommandations actionnables prioritisées
- Alertes sur anomalies et qualité des données
- Export PDF rapport complet + CSV données
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
05-agent-analyse-donnees/
├── app.py          # Interface Streamlit + visualisations Plotly
├── graph.py        # LangGraph 3 nœuds
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

Fichier `ventes_2026.csv` inclus — données de ventes fictives avec colonnes : date, produit, categorie, region, commercial, quantite, prix_unitaire, ca, marge, client.

Type d'analyse recommandé : **Analyse de performance commerciale**

## Modèles utilisés

- `claude-haiku-4-5-20251001` — analyse structure
- `claude-sonnet-4-6` — génération insights et recommandations