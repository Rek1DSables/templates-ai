# 34 — Agent de Trading Paper AI

Simulation de stratégies de trading algorithmique sur données réelles. LangGraph orchestre 4 nœuds en séquence : récupération des prix via yfinance, calcul des signaux techniques, simulation du portefeuille paper trading, analyse Claude des performances.

## Stack

- **LangGraph** — orchestration séquentielle des 4 nœuds
- **Anthropic Claude** — analyse des performances et recommandations
- **yfinance** — données de prix en temps réel
- **Pandas / NumPy** — calcul des indicateurs techniques
- **Plotly** — visualisation des courbes et signaux
- **Streamlit** — interface utilisateur

## Fonctionnalités

- 3 stratégies disponibles : Moyenne Mobile, RSI, Momentum
- 8 actifs disponibles : BTC-USD, ETH-USD, AAPL, MSFT, GOOGL, TSLA, NVDA, SP500
- 4 périodes : 1 mois, 3 mois, 6 mois, 1 an
- Capital initial configurable
- KPIs : valeur finale, rendement stratégie, comparaison Buy & Hold, nombre de trades
- Graphique d'évolution du portefeuille
- Graphique des cours avec signaux achat/vente
- Tableau des trades exécutés
- Analyse Claude en français des performances
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
34-agent-trading-paper/
├── app.py          # Interface Streamlit + Plotly
├── graph.py        # LangGraph 4 noeuds
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

- Actif : BTC-USD
- Strategie : Moyenne Mobile
- Periode : 3mo
- Capital : 10 000 USD

## Modèle utilisé

`claude-haiku-4-5-20251001`