# 09 — Analyse Sentiment & Reviews

Pipeline d'analyse automatique des avis clients : scraping via Apify → analyse sentiment → extraction des thèmes récurrents → rapport de synthèse téléchargeable.

**Stack :** LangGraph · Apify · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
validate_input → scrape_reviews → format_reviews → analyse_sentiment
→ extract_themes → generate_report
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
APIFY_API_KEY=apify_api_...
```

Clé Apify : [apify.com](https://apify.com) → Settings → Integrations → API token

---

## Sources supportées

| Source | Acteur Apify |
|---|---|
| Google Maps | `compass/google-maps-reviews-scraper` |
| Trustpilot | `misceres/trustpilot-scraper` |

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `MAX_REVIEWS` | Nombre max de reviews à récupérer (défaut : 50) |
| `SOURCES` | Sources disponibles dans le formulaire |