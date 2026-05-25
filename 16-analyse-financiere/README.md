# 16 — Agent d'Analyse Financière

Pipeline d'analyse financière automatisé : saisie des données → calcul des ratios → comparaison aux benchmarks sectoriels → interprétation IA → synthèse d'investissement.

**Stack :** LangGraph · Pandas · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
validate_input → calculate_ratios → compare_to_benchmark → interpret_results → generate_recommendation
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

## Ratios calculés

| Ratio | Description |
|---|---|
| Marge brute | Gross profit / Revenue |
| Marge nette | Net income / Revenue |
| ROE | Net income / Total equity |
| ROA | Net income / Total assets |
| Dette/Equity | Total debt / Total equity |
| Ratio courant | Current assets / Current liabilities |
| P/E | Market cap / Net income |

---

## Benchmarks sectoriels (config.py)

Secteurs disponibles : Technologie, Finance, Santé, Industrie, Distribution.
Les benchmarks sont personnalisables dans `config.py` sous `SECTOR_BENCHMARKS`.

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `SECTOR_BENCHMARKS` | Ratios moyens par secteur |
| `SECTORS` | Liste des secteurs disponibles |