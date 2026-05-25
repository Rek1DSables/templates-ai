# 20 — Agent de Formation & Quiz Adaptatif

Quiz adaptatif intelligent : génération de questions selon le niveau → évaluation des réponses → feedback personnalisé → progression automatique au niveau supérieur.

**Stack :** LangGraph · Supabase · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
generate_questions → evaluate_answers → generate_feedback → save_session
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
CREATE TABLE quiz_sessions (
    id           UUID        DEFAULT gen_random_uuid() PRIMARY KEY,
    learner_name TEXT        NOT NULL,
    topic        TEXT        NOT NULL,
    level        TEXT,
    score        NUMERIC,
    next_level   TEXT,
    questions    TEXT,
    answers      TEXT,
    feedback     TEXT,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);
```

---

## Fonctionnement

1. L'apprenant choisit un sujet et son niveau actuel
2. Le LLM génère des questions adaptées au niveau
3. L'apprenant répond aux questions
4. Le pipeline évalue et génère un feedback personnalisé
5. Si score ≥ seuil → passage automatique au niveau supérieur

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `QUESTIONS_PER_SESSION` | Nombre de questions par quiz (défaut : 5) |
| `PASS_THRESHOLD` | Score minimum pour progresser (défaut : 0.7 = 70%) |
| `LEVELS` | Niveaux disponibles |