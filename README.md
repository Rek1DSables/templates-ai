# Templates AI Automation — Portfolio Malt

Collection de 28 templates d'automatisation IA production-ready, construits avec LangGraph, CrewAI, Claude API et les stacks les plus demandées sur le marché freelance 2025-2026.

Chaque template est autonome, documenté et déployable en moins d'une heure.

---

## Stack principale

- **Orchestration** : LangGraph, CrewAI
- **LLM** : Anthropic Claude (Haiku + Sonnet selon les nœuds)
- **Interface** : Streamlit
- **Base de données** : Supabase (PostgreSQL)
- **Emails** : Gmail API (OAuth2)
- **Recherche web** : Serper
- **PDF** : FPDF2, PyMuPDF
- **RAG** : FAISS, HuggingFace
- **Data** : Pandas, Plotly, NumPy
- **Audio** : Whisper (OpenAI), gTTS / ElevenLabs

---

## Templates

| # | Nom | Stack | Niveau |
|---|-----|-------|--------|
| 01 | Lead Qualifier | LangGraph + Supabase + Gmail + Streamlit | Débutant |
| 02 | Agent Content Marketing Multicanal | LangGraph + Serper + FPDF2 + Streamlit | Intermédiaire |
| 03 | Agent de Veille Multi-Sources | LangGraph + Serper + Supabase + Streamlit | Intermédiaire |
| 04 | Dashboard Reporting & Analytics | LangGraph + Plotly + Supabase + FPDF2 + Streamlit | Intermédiaire |
| 05 | Chatbot RAG | LangGraph + FAISS + HuggingFace + Streamlit | Intermédiaire |
| 06 | Recrutement Automatisé | LangGraph + Supabase + PyMuPDF + Streamlit | Intermédiaire |
| 07 | Agent Finance & Documents | LangGraph + PyMuPDF + FPDF2 + Streamlit | Avancé |
| 08 | Monitoring & Alertes | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 09 | RAG Multi-Sources | LangGraph + FAISS + Supabase + Streamlit | Avancé |
| 10 | Formation & Quiz Adaptatif | LangGraph + Supabase + Streamlit | Avancé |
| 11 | Générateur de Newsletters | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 12 | Agent Scraping & Extraction | LangGraph + BeautifulSoup + Pandas + Streamlit | Avancé |
| 13 | Veille Légale & Réglementaire | LangGraph + Serper + Supabase + Streamlit | Avancé |
| 14 | Générateur de Contrats | LangGraph + FPDF2 + Supabase + Streamlit | Avancé |
| 15 | Onboarding Employé | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 16 | Transcription & Résumé Réunions | LangGraph + Supabase + Streamlit | Avancé |
| 17 | Analyseur d'Images & Documents | LangGraph + Claude Vision + Streamlit | Avancé |
| 18 | Agent de Recherche ReAct | LangGraph + Serper + Streamlit | Expert |
| 19 | Orchestrateur Multi-Agents | LangGraph + Serper + FPDF2 + Streamlit | Expert |
| 20 | Support Client Enterprise | LangGraph + Gmail + Supabase + Streamlit | Expert |
| 21 | Audit IA Interne | LangGraph + FPDF2 + Streamlit | Expert |
| 22 | Agent Vocal Entrant | LangGraph + Whisper + ElevenLabs + Streamlit | Expert |
| 23 | Générateur de Propositions Commerciales | LangGraph + FPDF2 + Supabase + Streamlit | Expert |
| 24 | Agent SEO | LangGraph + BeautifulSoup + Serper + FPDF2 + Streamlit | Expert |
| 25 | Générateur de Rapports Clients | LangGraph + FPDF2 + Supabase + Streamlit | Expert |
| 26 | Agent de Support Technique | LangGraph + Claude + Streamlit | Expert |
| 27 | Analyseur de Contrats | LangGraph + PyMuPDF + FPDF2 + Streamlit | Expert |
| 28 | Chatbot Multilingue | LangGraph + Supabase + Streamlit | Intermédiaire |

---

## Architecture LLM

Les templates utilisent deux modèles selon la nature des nœuds :

- **claude-haiku-4-5-20251001** — nœuds d'extraction, analyse, classification, JSON
- **claude-sonnet-4-6** — nœuds de génération longue (rapports, roadmaps, propales, analyses SEO)

Templates upgradés Sonnet sur les nœuds de génération : 03, 04, 19, 21, 23, 24. Le template 27 utilise Haiku avec split en 4 appels.

---

## Changer de provider LLM

Par défaut, tous les templates utilisent l'API Anthropic Claude. Il est possible de basculer sur un autre provider selon les besoins du client (coût, souveraineté, préférence technique).

**Providers compatibles**

| Provider | Modèle recommandé | Coût estimé vs Claude | Remarque |
|----------|-------------------|----------------------|----------|
| Anthropic (défaut) | claude-haiku-4-5 | référence | RGPD, serveurs EU |
| DeepSeek | deepseek-chat | ~10x moins cher | Serveurs Chine |
| OpenAI | gpt-4o-mini | ~2x moins cher | Serveurs US |
| Mistral | mistral-small | ~3x moins cher | Serveurs EU, RGPD |

**Migration en 3 étapes**

1. Installer le client alternatif :
```bash
pip install openai  # compatible DeepSeek, OpenAI et Mistral
```

2. Modifier `config.py` :
```python
# DeepSeek
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"
LLM_API_KEY = "sk-..."

# OpenAI
LLM_BASE_URL = "https://api.openai.com/v1"
LLM_MODEL = "gpt-4o-mini"
LLM_API_KEY = "sk-..."

# Mistral
LLM_BASE_URL = "https://api.mistral.ai/v1"
LLM_MODEL = "mistral-small-latest"
LLM_API_KEY = "..."
```

3. Remplacer le client dans `graph.py` :
```python
from openai import OpenAI
client = OpenAI(api_key=LLM_API_KEY, base_url=LLM_BASE_URL)
```

**Recommandation** : Anthropic reste le provider par défaut pour les clients avec des contraintes RGPD ou de confidentialité des données. DeepSeek est intéressant pour les projets internes sans données sensibles. Mistral est le meilleur compromis coût / souveraineté européenne.

---

## Estimation des coûts API

Coûts mensuels estimés avec Anthropic Claude Haiku (provider par défaut), selon le volume d'utilisation.

| Template | Usage léger | Usage moyen | Usage intensif |
|----------|-------------|-------------|----------------|
| 01 — Lead Qualifier | ~2€ | ~8€ | ~25€ |
| 03 — Veille Multi-Sources | ~3€ | ~12€ | ~35€ |
| 04 — Dashboard Reporting | ~2€ | ~7€ | ~20€ |
| 05 — Chatbot RAG | ~1€ | ~5€ | ~15€ |
| 07 — Finance & Documents | ~2€ | ~8€ | ~22€ |
| 12 — Scraping & Extraction | ~1€ | ~4€ | ~12€ |
| 19 — Orchestrateur | ~5€ | ~20€ | ~60€ |
| 21 — Audit IA | ~4€ | ~15€ | ~45€ |
| 23 — Propales | ~3€ | ~10€ | ~30€ |
| 24 — Agent SEO | ~5€ | ~18€ | ~55€ |
| 27 — Analyseur Contrats | ~2€ | ~8€ | ~25€ |
| 28 — Chatbot Multilingue | ~1€ | ~4€ | ~12€ |

*Usage léger : quelques utilisations/jour. Usage moyen : usage régulier en équipe. Usage intensif : usage production à fort volume.*

Avec DeepSeek, diviser ces estimations par 8 à 10. Avec Mistral Small, diviser par 3.

---

## Pipelines clients typiques

Les templates peuvent être combinés pour former des solutions complètes. Exemples de pipelines métier :

**Pipeline commercial complet**
```
01 — Lead Qualifier
      ↓ leads qualifiés
23 — Générateur de Propales
      ↓ propale signée
27 — Analyseur de Contrats
```
Cas d'usage : automatiser le cycle de vente de la qualification à la signature.

---

**Pipeline RH complet**
```
06 — Recrutement Automatisé
      ↓ candidat retenu
15 — Onboarding Employé
      ↓ collaborateur en poste
10 — Formation & Quiz Adaptatif
```
Cas d'usage : automatiser le cycle RH du recrutement à la formation.

---

**Pipeline marketing & veille**
```
03 — Veille Multi-Sources
      ↓ signaux détectés
02 — Agent Content Marketing
      ↓ contenus générés
11 — Générateur de Newsletters
```
Cas d'usage : transformer la veille en contenu publié automatiquement.

---

**Pipeline juridique & conformité**
```
13 — Veille Légale & Réglementaire
      ↓ évolutions identifiées
27 — Analyseur de Contrats
      ↓ contrats mis à jour
14 — Générateur de Contrats
```
Cas d'usage : surveiller les évolutions réglementaires et adapter les contrats en continu.

---

**Pipeline reporting & pilotage**
```
04 — Dashboard Reporting & Analytics
      ↓ KPIs consolidés
25 — Générateur de Rapports Clients
      ↓ rapport envoyé
08 — Monitoring & Alertes
```
Cas d'usage : automatiser le reporting client avec alertes en temps réel.

---

**Pipeline data & prospection**
```
12 — Agent Scraping & Extraction
      ↓ données extraites
01 — Lead Qualifier
      ↓ leads qualifiés
23 — Générateur de Propales
```
Cas d'usage : scraper des prospects, les qualifier automatiquement et générer une propale.

---

## Déploiement cloud

Chaque template Streamlit peut être déployé en production en quelques minutes.

**Streamlit Cloud (gratuit)**
```bash
# 1. Pusher le template sur GitHub (repo public ou privé)
# 2. Connecter sur share.streamlit.io
# 3. Configurer les secrets dans Settings > Secrets :
ANTHROPIC_API_KEY = "sk-ant-..."
SUPABASE_URL = "https://..."
SUPABASE_KEY = "..."
```

**Railway**
```bash
# Ajouter un fichier Procfile à la racine du template :
web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0

# Variables d'environnement à configurer dans Railway Dashboard
# Note : supprimer pywin32 du requirements.txt avant déploiement Linux
```

**Docker (auto-hébergement)**
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

## Personnalisation rapide

Variables clés à adapter par template sans toucher à la logique métier :

| Template | Variables personnalisables |
|----------|--------------------------|
| 01 — Lead Qualifier | Seuils hot/warm/cold, critères de scoring, template email |
| 03 — Veille | Sujets surveillés, secteur, type de veille, niveau d'alerte |
| 04 — Dashboard | KPIs suivis, secteur, période d'analyse |
| 05 — Chatbot RAG | Base de connaissance, ton de réponse |
| 06 — Recrutement | Critères CV, grille de scoring, templates email |
| 07 — Finance | Types de documents, taux de TVA, mentions légales |
| 10 — Formation | Thèmes, niveaux de difficulté, nombre de questions |
| 12 — Scraping | Types de données, champs personnalisés, nb URLs |
| 21 — Audit IA | Secteur, taille entreprise, budget IA |
| 23 — Propales | Types de mission, mode de facturation, expertise |
| 24 — SEO | URL cible, mots-clés, type de site, secteur |
| 27 — Contrats | Types de contrat, niveaux de risque |
| 28 — Chatbot | Base de connaissance, langues supportées |

---

## Installation générique

```bash
cd XX-nom-template
pip install -r requirements.txt
streamlit run app.py
```

Chaque template contient un fichier `.env` à configurer et un `README.md` avec les instructions complètes, le SQL Supabase si nécessaire et les données de test.

---

## Prérequis communs

- Python 3.10+
- Clé API Anthropic (ou provider alternatif)
- Compte Supabase (templates avec base de données)
- Compte Gmail + credentials OAuth2 (templates avec email)
- Clé Serper (templates avec recherche web)

---

## Positionnement

Templates produits par un développeur AI Automation freelance spécialisé dans la conception et le déploiement d'agents IA sur mesure.

**Disponible sur Malt** pour des missions de développement d'agents IA, pipelines d'automatisation et intégrations Claude API.

Stack : LangGraph · CrewAI · Claude API · MCP Protocol · Supabase · Streamlit

---

*Collection maintenue activement — nouveaux templates ajoutés régulièrement.*