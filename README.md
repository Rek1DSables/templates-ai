# Templates AI Automation — Portfolio Malt

Collection de 12 agents IA production-ready, construits avec LangGraph et Claude API. Chaque template cible un cas d'usage business à fort ROI, peu couvert par les solutions no-code ou les SaaS existants.

---

## Stack principale

- **Orchestration** : LangGraph (multi-agents, routeurs conditionnels, boucles)
- **LLM** : Anthropic Claude Haiku + Sonnet selon les nœuds
- **Interface** : Streamlit
- **Base de données** : Supabase (PostgreSQL)
- **Emails** : Gmail API (OAuth2)
- **Audio** : Whisper (OpenAI), ElevenLabs
- **Data** : Pandas, Plotly
- **PDF** : FPDF2, PyMuPDF
- **Recherche** : Serper, BeautifulSoup

---

## Templates

| # | Nom | Cas d'usage | Niveau |
|---|-----|-------------|--------|
| 01 | Lead Qualifier | Scoring et qualification automatique des leads entrants | Intermédiaire |
| 02 | Agent EU AI Act Compliance | Audit de conformité EU AI Act — classification, gaps, plan de remédiation, audit trail | Expert |
| 03 | Agent Finance Close | Clôture financière multi-agents — réconciliation, variances, journal entries, disclosure | Expert |
| 04 | Agent Analyse de Données | Upload CSV/Excel → insights IA → visualisations → rapport PDF | Avancé |
| 05 | Agent Email Entrant | Classification, réponse automatique et routing des emails entrants | Avancé |
| 06 | RAG Multi-Sources | Base de connaissance multi-documents avec retrieval augmenté | Expert |
| 07 | Agent Email en Masse | Génération d'emails ultra-personnalisés par contact + envoi Gmail | Avancé |
| 08 | Agent Due Diligence | Analyse M&A multi-axes — risques, scoring, matrice, verdict | Expert |
| 09 | Agent Scraping & Extraction | Extraction de données structurées depuis URLs ou texte brut | Avancé |
| 10 | Pipeline Contractuel | Analyse + génération de contrats avec scoring risques | Expert |
| 11 | Orchestrateur Multi-Agents | Pipeline multi-agents avec coordination et agrégation | Expert |
| 12 | Agent Vocal | Agent vocal inbound — transcription, analyse, réponse | Expert |

---

## Architecture LLM

Chaque template utilise deux modèles selon la nature des nœuds :

- **claude-haiku-4-5-20251001** — extraction, classification, JSON, analyse structurée
- **claude-sonnet-4-6** — génération longue, rapports, recommandations, disclosure

---

## Ce qui différencie cette collection

Les templates no-code (Make, Zapier, n8n) couvrent les automatisations simples. Cette collection cible ce qu'ils ne font pas :

- **Domaines régulés** : conformité EU AI Act, clôture financière IFRS/PCG, due diligence M&A
- **Audit trail et gouvernance** : chaque décision agent est horodatée et traçable
- **Multi-agents coordonnés** : plusieurs agents spécialisés qui collaborent sur un workflow complexe
- **Personnalisation métier profonde** : logique business encodée, pas des templates génériques

---

## Changer de provider LLM

Par défaut : Anthropic Claude (RGPD, serveurs EU). Migration en 3 étapes :

```bash
pip install openai  # compatible DeepSeek, OpenAI, Mistral
```

Dans `config.py` :
```python
# DeepSeek (~10x moins cher, serveurs Chine)
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"

# Mistral (~3x moins cher, serveurs EU)
LLM_BASE_URL = "https://api.mistral.ai/v1"
LLM_MODEL = "mistral-small-latest"

# OpenAI (~2x moins cher, serveurs US)
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o-mini"
```

Dans `graph.py` :
```python
from openai import OpenAI
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
```

---

## Estimation des coûts API

Avec Anthropic Claude Haiku + Sonnet (provider par défaut) :

| Template | Usage léger | Usage moyen | Usage intensif |
|----------|-------------|-------------|----------------|
| 02 — EU AI Act | ~3€ | ~12€ | ~35€ |
| 03 — Finance Close | ~4€ | ~15€ | ~45€ |
| 04 — Analyse Données | ~1€ | ~5€ | ~15€ |
| 07 — Email en Masse | ~3€ | ~10€ | ~30€ |
| 08 — Due Diligence | ~5€ | ~18€ | ~55€ |
| 10 — Pipeline Contractuel | ~3€ | ~10€ | ~30€ |

Avec DeepSeek : diviser par 8 à 10. Avec Mistral Small : diviser par 3.

---

## Pipelines clients typiques

**Pipeline commercial complet**
```
01 — Lead Qualifier → 07 — Email en Masse → 10 — Pipeline Contractuel
```

**Pipeline conformité IA**
```
02 — EU AI Act Compliance → 11 — Orchestrateur Multi-Agents
```

**Pipeline M&A / investissement**
```
09 — Scraping & Extraction → 08 — Due Diligence → 10 — Pipeline Contractuel
```

**Pipeline finance**
```
04 — Analyse Données → 03 — Finance Close
```

---

## Déploiement cloud

**Streamlit Cloud (gratuit)**
```bash
# Connecter sur share.streamlit.io
# Configurer secrets : ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
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

Chaque template contient un `.env` à configurer et un `README.md` avec instructions, données de test et SQL Supabase si nécessaire.

---

## Prérequis

- Python 3.10+
- Clé API Anthropic
- Compte Supabase (templates avec base de données)
- Compte Gmail + credentials OAuth2 (templates email)
- Clé Serper (templates avec recherche web)

---

## Positionnement

Agents IA production-ready développés par un consultant AI Automation freelance spécialisé LangGraph / Claude API / MCP Protocol.

**Disponible sur Malt** pour missions de développement d'agents IA sur mesure, pipelines d'automatisation métier et intégrations Claude API.

---

*Collection maintenue activement.*