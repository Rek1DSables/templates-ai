# Templates AI Automation — Portfolio Malt

Collection de 38 templates d'automatisation IA production-ready, construits avec LangGraph, CrewAI, Claude API et les stacks les plus demandées sur le marché freelance 2025-2026.

Chaque template est autonome, documenté et déployable en moins d'une heure.

---

## Stack principale

- **Orchestration** : LangGraph, CrewAI
- **LLM** : Anthropic Claude (claude-haiku-4-5-20251001)
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
| 01 | Chatbot FAQ | LangGraph + FAISS + Streamlit | Débutant |
| 02 | Lead Qualifier | LangGraph + Supabase + Gmail + Streamlit | Débutant |
| 03 | Générateur de contenu | CrewAI + Serper + Streamlit | Débutant |
| 04 | Veille concurrentielle | CrewAI + Serper + Streamlit | Débutant |
| 05 | Résumeur de documents | LangGraph + PyPDF + Streamlit | Débutant |
| 06 | Extracteur de données web | LangGraph + BeautifulSoup + Streamlit | Débutant |
| 07 | Support client multi-canal | LangGraph + Supabase + Streamlit | Intermédiaire |
| 08 | Onboarding client | LangGraph + Gmail + Supabase + Streamlit | Intermédiaire |
| 09 | Analyse sentiment | LangGraph + Apify + Streamlit | Intermédiaire |
| 10 | Générateur de rapports | LangGraph + Pandas + FPDF2 + Streamlit | Intermédiaire |
| 11 | Prospection LinkedIn | LangGraph + Streamlit | Intermédiaire |
| 12 | Chatbot RAG | LangGraph + FAISS + HuggingFace + Streamlit | Intermédiaire |
| 13 | Suivi de projet | LangGraph + Supabase + Streamlit | Intermédiaire |
| 14 | Recrutement automatisé | LangGraph + Supabase + PyMuPDF + Streamlit | Intermédiaire |
| 15 | Research & Reporting | CrewAI + Serper + Streamlit | Avancé |
| 16 | Analyse financière | LangGraph + Pandas + Streamlit | Avancé |
| 17 | Automatisation comptable | LangGraph + PyMuPDF + Supabase + Streamlit | Avancé |
| 18 | Monitoring & Alertes | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 19 | RAG Multi-Sources | LangGraph + FAISS + Supabase + Streamlit | Avancé |
| 20 | Formation & Quiz Adaptatif | LangGraph + Supabase + Streamlit | Avancé |
| 21 | Générateur de newsletters | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 22 | Agent réseaux sociaux | LangGraph + Serper + Streamlit | Avancé |
| 23 | Générateur de devis | LangGraph + FPDF2 + Supabase + Streamlit | Avancé |
| 24 | Pipeline E-commerce | LangGraph + Supabase + Gmail + Streamlit | Avancé |
| 25 | Agent CRM | LangGraph + Supabase + Streamlit | Avancé |
| 26 | Dashboard Analytics | LangGraph + Pandas + Plotly + Streamlit | Avancé |
| 27 | Agent de Prédiction | LangGraph + NumPy + Plotly + Streamlit | Avancé |
| 28 | Veille légale & réglementaire | LangGraph + Serper + Supabase + Streamlit | Avancé |
| 29 | Générateur de contrats | LangGraph + FPDF2 + Supabase + Streamlit | Avancé |
| 30 | Onboarding employé | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 31 | Transcription & résumé réunions | LangGraph + Supabase + Streamlit | Avancé |
| 32 | Analyseur d'images & documents | LangGraph + Claude Vision + Streamlit | Avancé |
| 33 | Agent de recherche ReAct | LangGraph + Serper + Streamlit | Expert |
| 34 | Agent de trading paper | LangGraph + yfinance + Plotly + Streamlit | Expert |
| 35 | Orchestrateur multi-agents | LangGraph + Serper + FPDF2 + Streamlit | Expert |
| 36 | Support client enterprise | LangGraph + Gmail + Supabase + Streamlit | Expert |
| 37 | Audit IA interne | LangGraph + FPDF2 + Streamlit | Expert |
| 38 | Agent vocal entrant | LangGraph + Whisper + ElevenLabs + Streamlit | Expert |

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
- Clé API Anthropic
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