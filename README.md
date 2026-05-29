# Templates AI Automation — Portfolio Malt

Collection de 12 agents IA production-ready, positionnés sur les niches à forte demande et faible offre en 2026. Chaque template cible un cas d'usage business à fort ROI, inaccessible aux solutions no-code ou aux SaaS génériques.

---

## Positionnement

Cette collection cible les 3 niveaux qui justifient 800€+/jour :

- **Agents verticaux spécialisés** — logique métier encodée, domaines régulés, forte barrière à l'entrée
- **Architectures multi-agents** — orchestration LangGraph, mémoire partagée, gestion des conflits
- **Gouvernance enterprise** — audit trail horodaté, permissions, conformité réglementaire

Ce que les SaaS et le no-code ne font pas : intégration profonde dans le SI existant, audit trail pour conformité, logique métier custom, gouvernance des données sensibles.

---

## Templates

| # | Nom | Cas d'usage | Niveau marché |
|---|-----|-------------|---------------|
| 01 | Agent Workflow B2B | Email → CRM lookup → Classification → Ticket → Réponse → Gmail | 🔴 Expert |
| 02 | Agent EU AI Act Compliance | Audit conformité EU AI Act — classification, gaps, plan remédiation, audit trail | 🔴 Expert |
| 03 | Agent Finance Close | Clôture financière multi-agents — réconciliation, variances, journal entries, disclosure | 🔴 Expert |
| 04 | Agent SDR / Revenue | Enrichissement → Scoring ICP → Séquence 3 emails → Envoi Gmail | 🔴 Expert |
| 05 | Agent Data Analyst Autonome | Question langage naturel → SQL → Exécution → Insights → Commentaire exécutif | 🔴 Expert |
| 06 | Agent RAG Enterprise | Base de connaissance privée avec gouvernance, permissions, anti-hallucination, audit trail | 🔴 Expert |
| 07 | Agent Analyse Documentaire | Extraction structurée → Vérification risques → Synthèse → Matrice risques → PDF | 🔴 Expert |
| 08 | Agent Due Diligence M&A | Analyse multi-axes → Scoring → Matrice risques → Verdict → Fourchette valorisation | 🔴 Expert |
| 09 | Agent Monitoring & Alertes | Détection violations → Analyse causale → Alertes graduées → Gmail → Supabase | 🔴 Expert |
| 10 | Agent Pipeline Contractuel | Extraction clauses → Analyse risques → Synthèse → Génération contrat amélioré | 🔴 Expert |
| 11 | Agent Évaluation Qualité LLM | Tests → Scoring 7 dimensions → Régressions → Badge déployabilité → Rapport | 🔴 Expert |
| 12 | Agent Intégration SI & Webhook | Réception → Validation → Mapping → Retry → Dead Letter → Multi-destinations | 🔴 Expert |

---

## Stack principale

- **Orchestration** : LangGraph (multi-agents, routeurs conditionnels, boucles)
- **LLM** : Anthropic Claude Haiku + Sonnet selon les nœuds
- **Interface** : Streamlit
- **Base de données** : Supabase (PostgreSQL)
- **Emails** : Gmail API (OAuth2)
- **Recherche web** : Serper
- **Embeddings** : Sentence Transformers (multilingue)
- **Data** : Pandas, Plotly
- **PDF** : FPDF2, PyMuPDF
- **HTTP** : Requests (webhooks, APIs tierces)

---

## Architecture LLM

Chaque template utilise deux modèles selon la nature des nœuds :

- **claude-haiku-4-5-20251001** — extraction, classification, validation, JSON, analyse structurée
- **claude-sonnet-4-6** — génération longue, rapports, recommandations, synthèses

---

## Changer de provider LLM

Par défaut : Anthropic Claude (RGPD, serveurs EU).

| Provider | Modèle | Coût vs Claude | Remarque |
|----------|--------|----------------|----------|
| Anthropic (défaut) | claude-haiku-4-5 | référence | RGPD, serveurs EU |
| DeepSeek | deepseek-chat | ~10x moins cher | Serveurs Chine |
| Mistral | mistral-small | ~3x moins cher | Serveurs EU, RGPD |
| OpenAI | gpt-4o-mini | ~2x moins cher | Serveurs US |

Migration en 3 étapes :

```bash
pip install openai
```

Dans `config.py` :
```python
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "sk-..."
```

Dans `graph.py` :
```python
from openai import OpenAI
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
```

---

## Estimation des coûts API

Avec Anthropic Claude Haiku + Sonnet :

| Template | Usage léger | Usage moyen | Usage intensif |
|----------|-------------|-------------|----------------|
| 01 — Workflow B2B | ~2€ | ~8€ | ~25€ |
| 02 — EU AI Act | ~4€ | ~15€ | ~45€ |
| 03 — Finance Close | ~5€ | ~18€ | ~55€ |
| 04 — SDR Revenue | ~3€ | ~12€ | ~35€ |
| 05 — Data Analyst | ~2€ | ~7€ | ~20€ |
| 06 — RAG Enterprise | ~3€ | ~10€ | ~30€ |
| 07 — Analyse Doc | ~4€ | ~14€ | ~42€ |
| 08 — Due Diligence | ~5€ | ~18€ | ~55€ |
| 09 — Monitoring | ~2€ | ~8€ | ~24€ |
| 10 — Contractuel | ~3€ | ~12€ | ~36€ |
| 11 — Évaluation LLM | ~2€ | ~8€ | ~24€ |
| 12 — Intégration SI | ~2€ | ~7€ | ~20€ |

Avec DeepSeek : diviser par 8 à 10. Avec Mistral Small : diviser par 3.

---

## Pipelines clients typiques

**Pipeline commercial B2B complet**
```
04 — SDR Revenue → 01 — Workflow B2B → 10 — Pipeline Contractuel
```
Scraper les prospects → qualifier → traiter les réponses → générer le contrat

---

**Pipeline conformité IA (deadline août 2026)**
```
02 — EU AI Act Compliance → 11 — Évaluation Qualité LLM
```
Auditer les systèmes IA → valider la qualité avant déploiement

---

**Pipeline M&A / investissement**
```
07 — Analyse Documentaire → 08 — Due Diligence → 10 — Pipeline Contractuel
```
Analyser les documents → due diligence → générer les accords

---

**Pipeline finance enterprise**
```
05 — Data Analyst → 03 — Finance Close → 09 — Monitoring
```
Analyser les données → clôturer → monitorer en continu

---

**Pipeline SI & données**
```
12 — Intégration SI → 06 — RAG Enterprise → 05 — Data Analyst
```
Ingérer les événements → enrichir la base de connaissance → analyser

---

## Déploiement cloud

**Streamlit Cloud (gratuit)**
```bash
# Connecter sur share.streamlit.io
# Secrets : ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
```

**Railway**
```bash
# Procfile : web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
# Supprimer pywin32 du requirements.txt avant déploiement Linux
```

**Docker**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
```

---

## Installation

```bash
cd XX-nom-template
pip install -r requirements.txt
streamlit run app.py
```

Chaque template contient un `.env` à configurer et un `README.md` avec instructions complètes et données de test.

---

## Prérequis communs

- Python 3.10+
- Clé API Anthropic
- Compte Supabase (templates avec persistance)
- Compte Gmail + credentials OAuth2 (templates avec email)
- Clé Serper (template SDR avec enrichissement web)

---

## Disponible sur Malt

Consultant AI Automation freelance spécialisé dans la conception et le déploiement d'agents IA sur mesure.

Stack : LangGraph · Claude API · MCP Protocol · Supabase · Streamlit · LangGraph multi-agents

---

*Collection maintenue activement.*