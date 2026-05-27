# Templates AI Automation — Portfolio Malt

Collection de 23 templates d'automatisation IA production-ready, construits avec LangGraph, CrewAI, Claude API et les stacks les plus demandées sur le marché freelance 2025-2026.

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
| 01 | Lead Qualifier | LangGraph + Supabase + Gmail + Streamlit | Débutant |
| 02 | Agent Content Marketing Multicanal | LangGraph + Serper + FPDF2 + Streamlit | Intermédiaire |
| 03 | Agent de Veille Multi-Sources | LangGraph + Serper + Supabase + Streamlit | Intermédiaire |
| 04 | Dashboard Reporting & Analytics | LangGraph + Plotly + Supabase + FPDF2 + Streamlit | Intermédiaire |
| 05 | Chatbot RAG | LangGraph + FAISS + HuggingFace + Streamlit | Intermédiaire |
| 06 | Recrutement Automatisé | LangGraph + Supabase + PyMuPDF + Streamlit | Intermédiaire |
| 07 | Automatisation Comptable | LangGraph + PyMuPDF + Supabase + Streamlit | Avancé |
| 08 | Monitoring & Alertes | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 09 | RAG Multi-Sources | LangGraph + FAISS + Supabase + Streamlit | Avancé |
| 10 | Formation & Quiz Adaptatif | LangGraph + Supabase + Streamlit | Avancé |
| 11 | Générateur de Newsletters | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 12 | Générateur de Devis | LangGraph + FPDF2 + Supabase + Streamlit | Avancé |
| 13 | Veille Légale & Réglementaire | LangGraph + Serper + Supabase + Streamlit | Avancé |
| 14 | Générateur de Contrats | LangGraph + FPDF2 + Supabase + Streamlit | Avancé |
| 15 | Onboarding Employé | LangGraph + Gmail + Supabase + Streamlit | Avancé |
| 16 | Transcription & Résumé Réunions | LangGraph + Supabase + Streamlit | Avancé |
| 17 | Analyseur d'Images & Documents | LangGraph + Claude Vision + Streamlit | Avancé |
| 18 | Agent de Recherche ReAct | LangGraph + Serper + Streamlit | Expert |
| 19 | Agent de Trading Paper | LangGraph + yfinance + Plotly + Streamlit | Expert |
| 20 | Orchestrateur Multi-Agents | LangGraph + Serper + FPDF2 + Streamlit | Expert |
| 21 | Support Client Enterprise | LangGraph + Gmail + Supabase + Streamlit | Expert |
| 22 | Audit IA Interne | LangGraph + FPDF2 + Streamlit | Expert |
| 23 | Agent Vocal Entrant | LangGraph + Whisper + ElevenLabs + Streamlit | Expert |

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