Chaque nœud est fault-tolerant : toute erreur est capturée et le pipeline s'arrête proprement.

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
CREATE TABLE onboarding_clients (
    id                    UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    name                  TEXT        NOT NULL,
    email                 TEXT        NOT NULL,
    company               TEXT,
    sector                TEXT,
    project_description   TEXT,
    status                TEXT        DEFAULT 'pending',
    welcome_sent_at       TIMESTAMPTZ,
    questionnaire_sent_at TIMESTAMPTZ,
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Gmail OAuth2

1. Google Cloud Console → Activer l'API Gmail
2. Créer des identifiants OAuth2 → Application de bureau
3. Télécharger `credentials.json` → placer à la racine du projet
4. Le `token.json` se génère automatiquement au premier lancement

> ⚠️ Ne jamais versionner `credentials.json` et `token.json`

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom affiché dans les emails et l'interface |
| `COMPANY_SIGNATURE` | Signature automatique ajoutée à chaque email |
| `SUPABASE_TABLE` | Nom de la table Supabase |
| `SECTORS` | Liste des secteurs du formulaire |