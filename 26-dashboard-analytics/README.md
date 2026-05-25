# 26 — Dashboard Analytics Automatique

Pipeline d'analyse de données : upload CSV/Excel → statistiques automatiques → visualisations Plotly → insights IA → recommandations stratégiques.

**Stack :** LangGraph · Pandas · Plotly · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
load_data → compute_stats → generate_insights → generate_recommendations
```

---

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Variables d'environnement (.env)

```env
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Formats supportés

| Format | Extension |
|---|---|
| CSV | `.csv` |
| Excel | `.xlsx`, `.xls` |

---

## Fonctionnement

1. Upload d'un fichier CSV ou Excel
2. Détection automatique des colonnes date et numériques
3. Calcul des statistiques (sum, mean, max, min, médiane)
4. Détection des tendances (évolution première vs deuxième moitié)
5. Génération de graphiques automatiques (line, bar, scatter)
6. Insights IA et recommandations stratégiques

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom affiché dans l'interface |
| `PERIODS` | Périodes d'analyse disponibles |