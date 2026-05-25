# 22 — Agent Réseaux Sociaux

Pipeline de génération de contenu réseaux sociaux : recherche des tendances → rédaction de posts adaptés à chaque plateforme → planning de publication hebdomadaire.

**Stack :** LangGraph · Serper · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
research_trends → generate_posts → generate_planning
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
SERPER_API_KEY=...
```

---

## Plateformes supportées

| Plateforme | Limite | Format |
|---|---|---|
| LinkedIn | 1200 caractères | Professionnel, storytelling |
| Twitter/X | 280 caractères | Court, percutant |
| Instagram | 2200 caractères | Émotionnel, visuel |
| Facebook | 500 caractères | Conversationnel |

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `COMPANY_NAME` | Nom de l'entreprise |
| `COMPANY_SECTOR` | Secteur d'activité |
| `TARGET_AUDIENCE` | Audience cible |
| `POSTS_PER_WEEK` | Posts par semaine dans le planning |
| `PLATFORMS` | Plateformes disponibles |