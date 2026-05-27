# 14 — Recrutement Automatisé

Pipeline de recrutement intelligent : analyse automatique de CV par IA, scoring par rapport à la fiche de poste, suivi des candidats et résumé du pipeline.

**Stack :** LangGraph · Supabase · PyMuPDF · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
route_action → extract_cv_text → analyze_cv | update_status | get_pipeline
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
SUPABASE_URL=https://xxxx.supabase.co
SUPABASE_KEY=eyJ...
```

---

## Table Supabase

```sql
CREATE TABLE candidates (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    name            TEXT        NOT NULL,
    cv_name         TEXT,
    job_description TEXT,
    analysis        TEXT,
    status          TEXT        DEFAULT 'Nouveau',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ
);
```

---

## Fonctionnement

- **Pipeline** : vue d'ensemble des candidats + résumé IA
- **Analyser un CV** : upload PDF + fiche de poste → analyse et scoring automatique
- **Mettre à jour** : changement de statut par ID candidat

---

## Statuts disponibles

`Nouveau` → `Présélectionné` → `Entretien` → `Offre envoyée` → `Embauché` / `Refusé`

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `SUPABASE_TABLE` | Nom de la table (défaut : `candidates`) |
| `CANDIDATE_STATUSES` | Liste des statuts disponibles |