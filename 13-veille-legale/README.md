# 28 — Agent de Veille Légale & Réglementaire

Pipeline de veille juridique automatisée : recherche des actualités réglementaires → extraction des mises à jour → analyse d'impact sur l'entreprise → plan d'action de mise en conformité.

**Stack :** LangGraph · Serper · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
search_legal_updates → extract_legal_updates → analyse_impact → generate_action_plan → save_to_supabase
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
SERPER_API_KEY=...
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## Table Supabase

```sql
CREATE TABLE legal_watches (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name    TEXT        NOT NULL,
    legal_domain    TEXT,
    jurisdiction    TEXT,
    legal_updates   TEXT,
    impact_analysis TEXT,
    action_plan     TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Domaines juridiques supportés

- RGPD & Protection des données
- Droit du travail
- Droit des sociétés
- Fiscalité & TVA
- Droit de la consommation
- Propriété intellectuelle
- Cybersécurité & NIS2
- IA & Réglementation (AI Act)
- Droit commercial

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `LEGAL_DOMAINS` | Domaines juridiques disponibles |
| `JURISDICTIONS` | Juridictions disponibles |