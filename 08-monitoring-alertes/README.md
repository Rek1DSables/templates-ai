# 18 — Agent Monitoring & Alertes Intelligentes

Pipeline de monitoring intelligent : saisie des métriques → détection des anomalies → analyse IA de la cause probable → enregistrement Supabase → alerte email si critique.

**Stack :** LangGraph · Gmail · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
detect_anomalies → analyse_anomalies → save_alert → send_alert_email
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
SENDER_EMAIL=expediteur@gmail.com
ALERT_EMAIL=destinataire@gmail.com
```

---

## Table Supabase

```sql
CREATE TABLE monitoring_alerts (
    id         UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    context    TEXT,
    metrics    TEXT,
    anomalies  TEXT,
    analysis   TEXT,
    has_alert  BOOLEAN     DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Niveaux d'alerte

| Niveau | Condition |
|---|---|
| 🟢 OK | Valeur sous le seuil |
| 🟡 Avertissement | Valeur ≥ seuil |
| 🔴 Critique | Valeur ≥ 120% du seuil |

Email automatique envoyé uniquement en cas d'alerte critique.

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `DEFAULT_THRESHOLDS` | Seuils par défaut pour chaque métrique |
| `ALERT_LEVELS` | Ratios définissant les niveaux d'alerte |
| `METRICS` | Liste des métriques surveillées |