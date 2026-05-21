# 10 — Générateur de Rapports Automatiques

Pipeline de génération automatique de rapports : upload CSV/Excel → analyse statistique → interprétation IA → recommandations → rapport PDF téléchargeable.

**Stack :** LangGraph · Pandas · FPDF2 · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
load_file → compute_stats → interpret_data → generate_recommendations → generate_pdf
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

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom affiché dans le rapport PDF |
| `REPORT_TITLE` | Titre du rapport |
| `MAX_ROWS_PREVIEW` | Nombre de lignes envoyées au LLM (défaut : 50) |