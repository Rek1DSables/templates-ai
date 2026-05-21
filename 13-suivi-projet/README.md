# 13 — Suivi de Projet Automatisé

Outil de gestion de projet avec résumé IA automatique : ajout, modification, suppression de tâches via Supabase + analyse intelligente de l'avancement du projet.

**Stack :** LangGraph · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
route_action → add_task | update_task | delete_task | get_summary
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
CREATE TABLE project_tasks (
    id          UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    task_name   TEXT        NOT NULL,
    description TEXT,
    status      TEXT        DEFAULT 'À faire',
    priority    TEXT        DEFAULT 'Moyenne',
    assignee    TEXT,
    due_date    DATE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ
);
```

---

## Fonctionnement

- **Tableau de bord** : métriques + résumé IA de l'avancement
- **Ajouter une tâche** : formulaire complet avec statut, priorité, assigné, échéance
- **Modifier / Supprimer** : mise à jour ou suppression par ID

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `SUPABASE_TABLE` | Nom de la table (défaut : `project_tasks`) |
| `TASK_STATUSES` | Liste des statuts disponibles |
| `TASK_PRIORITIES` | Liste des priorités disponibles |