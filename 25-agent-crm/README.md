# 25 — Agent CRM Intelligent

Pipeline CRM complet : gestion des contacts, suivi des opportunités, enregistrement des interactions et analyse IA du pipeline commercial.

**Stack :** LangGraph · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
route_action → add_contact | add_interaction | update_stage | get_pipeline | get_contact_summary
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

## Tables Supabase

```sql
CREATE TABLE crm_contacts (
    id         UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    name       TEXT        NOT NULL,
    email      TEXT,
    company    TEXT,
    phone      TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE crm_opportunities (
    id           UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_id   UUID        REFERENCES crm_contacts(id),
    contact_name TEXT,
    company      TEXT,
    stage        TEXT        DEFAULT 'Prospect',
    deal_value   NUMERIC     DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    updated_at   TIMESTAMPTZ
);

CREATE TABLE crm_interactions (
    id               UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    contact_id       UUID        REFERENCES crm_contacts(id),
    interaction_type TEXT,
    note             TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Fonctionnement

- **Pipeline** : vue Kanban par étape + résumé IA + valeur totale
- **Nouveau contact** : création contact + opportunité associée
- **Interactions** : enregistrement des échanges + mise à jour étape
- **Fiche contact** : historique complet + analyse IA + score opportunité

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `PIPELINE_STAGES` | Étapes du pipeline commercial |
| `INTERACTION_TYPES` | Types d'interactions disponibles |