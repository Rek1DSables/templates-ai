# 27 — Agent de Prédiction — Time Series

Pipeline de prédiction de séries temporelles : upload données → modèle de prédiction → visualisation avec intervalle de confiance → interprétation IA → recommandations stratégiques.

**Stack :** LangGraph · NumPy · Pandas · Plotly · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
load_data → run_forecast → interpret_forecast → generate_recommendations
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

## Modèles disponibles

| Modèle | Description |
|---|---|
| Moyenne mobile | Lisse les fluctuations court terme |
| Régression linéaire | Détecte les tendances long terme |
| Lissage exponentiel | Donne plus de poids aux données récentes |

---

## Métriques calculées

| Métrique | Description |
|---|---|
| MAE | Erreur absolue moyenne |
| RMSE | Racine de l'erreur quadratique moyenne |
| MAPE | Erreur relative en % |

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `FORECAST_PERIODS` | Nombre de périodes prédites par défaut (défaut : 30) |
| `CONFIDENCE_LEVEL` | Niveau de confiance de l'intervalle (défaut : 95%) |
| `MODELS` | Modèles disponibles |