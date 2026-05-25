# 23 — Générateur de Devis Automatique

Pipeline de génération de devis : analyse du projet → chiffrage IA → PDF professionnel téléchargeable → enregistrement Supabase.

**Stack :** LangGraph · FPDF2 · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
generate_line_items → generate_pdf → save_to_supabase
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
SENDER_EMAIL=ton-email@gmail.com
```

---

## Table Supabase

```sql
CREATE TABLE quotes (
    id                  UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    quote_number        TEXT        NOT NULL,
    client_name         TEXT        NOT NULL,
    client_email        TEXT,
    client_company      TEXT,
    project_description TEXT,
    total_ht            NUMERIC,
    total_tva           NUMERIC,
    total_ttc           NUMERIC,
    validity_date       TEXT,
    status              TEXT        DEFAULT 'envoyé',
    created_at          TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Fonctionnement

1. Saisie des informations client et description du projet
2. Le LLM génère des lignes de devis adaptées au budget
3. Calcul automatique HT / TVA / TTC
4. Génération d'un PDF professionnel téléchargeable
5. Enregistrement dans Supabase avec historique

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom affiché sur le devis |
| `COMPANY_ADDRESS` | Adresse du prestataire |
| `COMPANY_SIRET` | SIRET du prestataire |
| `TVA_RATE` | Taux de TVA (défaut : 20%) |
| `PAYMENT_TERMS` | Délai de paiement en jours (défaut : 30) |