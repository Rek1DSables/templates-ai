# 21 — Générateur de Newsletters Automatiques

Pipeline de génération et d'envoi automatique de newsletters : rédaction IA personnalisée → gestion des abonnés → envoi Gmail en masse.

**Stack :** LangGraph · Gmail · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
generate_subject → generate_content → fetch_subscribers → send_newsletter
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
CREATE TABLE newsletter_subscribers (
    id         UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    name       TEXT,
    email      TEXT        NOT NULL UNIQUE,
    active     BOOLEAN     DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Fonctionnement

- **Prévisualiser** : génère le contenu sans envoyer
- **Générer & Envoyer** : génère et envoie à tous les abonnés actifs
- **Gestion abonnés** : ajout et suivi des abonnés via Supabase

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom affiché dans la signature |
| `UNSUBSCRIBE_URL` | Lien de désabonnement |
| `TONES` | Tonalités disponibles |
