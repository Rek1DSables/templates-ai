# 24 — Pipeline E-commerce Automatisé

Pipeline de gestion e-commerce : commandes, stock, alertes intelligentes et dashboard IA.

**Stack :** LangGraph · Supabase · Gmail · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
route_action → new_order | update_status | get_dashboard | check_alerts
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
ALERT_EMAIL=ton-email@gmail.com
```

---

## Tables Supabase

```sql
CREATE TABLE products (
    id         UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
    name       TEXT    NOT NULL,
    price      NUMERIC NOT NULL,
    stock      INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE orders (
    id             UUID    DEFAULT gen_random_uuid() PRIMARY KEY,
    customer_name  TEXT    NOT NULL,
    customer_email TEXT,
    product_id     UUID    REFERENCES products(id),
    product_name   TEXT,
    quantity       INTEGER NOT NULL,
    unit_price     NUMERIC,
    total          NUMERIC,
    status         TEXT    DEFAULT 'En attente',
    created_at     TIMESTAMPTZ DEFAULT NOW(),
    updated_at     TIMESTAMPTZ
);
```

---

## Fonctionnement

- **Dashboard** : CA total, commandes récentes, état du stock + résumé IA
- **Nouvelle commande** : vérification stock → création commande → mise à jour stock
- **Mettre à jour** : changement de statut par ID commande
- **Alertes** : détection stock faible + commandes haute valeur + email automatique

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `LOW_STOCK_THRESHOLD` | Seuil d'alerte stock faible (défaut : 10) |
| `HIGH_VALUE_ORDER` | Seuil commande haute valeur (défaut : 500€) |
| `ORDER_STATUSES` | Statuts disponibles |