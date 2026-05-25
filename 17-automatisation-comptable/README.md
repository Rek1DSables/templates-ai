# 17 — Pipeline Automatisation Comptable

Pipeline de traitement automatique des factures : upload PDF → extraction des données → validation des montants → enregistrement Supabase.

**Stack :** LangGraph · PyMuPDF · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
extract_text → extract_invoice_data → validate_data → save_to_supabase
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
CREATE TABLE invoices (
    id              UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    supplier_name   TEXT,
    supplier_siret  TEXT,
    invoice_number  TEXT,
    invoice_date    DATE,
    due_date        DATE,
    amount_ht       NUMERIC,
    tva_rate        NUMERIC,
    tva_amount      NUMERIC,
    amount_ttc      NUMERIC,
    description     TEXT,
    category        TEXT,
    file_name       TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Données extraites automatiquement

- Fournisseur + SIRET
- Numéro et date de facture
- Date d'échéance
- Montants HT, TVA, TTC
- Catégorie comptable
- Description des services

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `SUPABASE_TABLE` | Nom de la table (défaut : `invoices`) |
| `EXPENSE_CATEGORIES` | Catégories comptables disponibles |
| `TVA_RATES` | Taux de TVA supportés |