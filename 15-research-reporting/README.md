# 15 — Système Multi-Agents Research & Reporting

Pipeline multi-agents collaboratif : 4 agents IA spécialisés produisent un rapport de marché complet sur n'importe quel secteur ou entreprise.

**Stack :** CrewAI · Serper · Streamlit  
**Modèle :** `claude-haiku-4-5-20251001`

---

## Agents

```
Searcher → Analyst → Writer → Critic
```

| Agent | Rôle |
|---|---|
| 🔍 Searcher | Collecte les informations via Google |
| 📊 Analyst | Analyse et identifie les tendances |
| ✍️ Writer | Rédige le rapport structuré |
| 🔎 Critic | Révise et améliore le rapport final |

---

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## Variables d'environnement (.env)

```env
SERPER_API_KEY=...
ANTHROPIC_API_KEY=sk-ant-...
```

---

## Personnalisation (config.py)

| Variable | Description |
|---|---|
| `MAX_SEARCH_RESULTS` | Résultats par recherche Serper (défaut : 5) |
| `COMPANY_NAME` | Nom affiché dans le rapport |