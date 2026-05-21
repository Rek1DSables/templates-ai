# 11 — Prospection LinkedIn Automatisée

Pipeline de prospection B2B : saisie manuelle des profils → scoring IA → rédaction de messages personnalisés.

**Stack :** LangGraph · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Pipeline

```
validate_input → score_profiles → draft_messages
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
```

---

## Fonctionnement

1. Renseignez jusqu'à 5 profils manuellement (nom, poste, entreprise, résumé)
2. Le pipeline score chaque profil sur 10 selon votre offre
3. Un message personnalisé est rédigé pour les profils avec un score ≥ 6/10

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `MAX_PROFILES` | Nombre max de profils à traiter (défaut : 20) |