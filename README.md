# Templates AI Automation

Collection de templates production-ready pour l'automatisation IA — construits avec LangGraph, CrewAI et l'API Anthropic.

Chaque template est **autonome**, **configurable** et **deployable** sans modifier le code metier.

---

## Templates disponibles

### Niveau 1 — Debutant (1-3 jours de livraison client)

| # | Template | Stack | Cas d'usage |
|---|----------|-------|-------------|
| 01 | [Chatbot FAQ intelligent](./01-chatbot-faq/) | LangGraph + FAISS + Streamlit | Repondre aux questions sur vos documents PDF |
| 02 | [Pipeline de qualification de leads](./02-lead-qualifier/) | LangGraph + Supabase + Streamlit | Scorer et router automatiquement vos prospects |
| 03 | [Generateur de contenu marketing](./03-content-generator/) | CrewAI + Serper + Streamlit | Produire articles, posts LinkedIn, newsletters |
| 04 | [Agent de veille concurrentielle](./04-competitive-watch/) | CrewAI + Serper + Streamlit | Analyser vos concurrents et generer un rapport |
| 05 | [Resumeur de documents](./05-document-summarizer/) | LangGraph + PyPDF + Streamlit | Resumer automatiquement vos PDFs |
| 06 | [Extracteur de donnees web](./06-web-extractor/) | LangGraph + BeautifulSoup + Streamlit | Extraire et structurer les donnees de n'importe quelle page web |

### Niveau 2 — Intermediaire (3-7 jours de livraison client)

| # | Template | Stack | Cas d'usage |
|---|----------|-------|-------------|
| 07 | [Support client multi-canal](./07-support-client/) | LangGraph + Supabase + Streamlit | Qualifier et router les tickets support |
| 08 | [Onboarding client automatise](./08-onboarding-client/) | LangGraph + Gmail + Supabase + Streamlit | Accueillir et qualifier automatiquement les nouveaux clients |
| 09 | [Analyse sentiment & reviews](./09-analyse-sentiment/) | LangGraph + Apify + Streamlit | Analyser les avis clients et generer un rapport |
| 10 | [Generateur de rapports automatiques](./10-generateur-rapports/) | LangGraph + Pandas + FPDF2 + Streamlit | Transformer des donnees CSV/Excel en rapport PDF |
| 11 | [Prospection LinkedIn](./11-prospection-linkedin/) | LangGraph + Streamlit | Scorer des profils et rediger des messages personnalises |
| 12 | [Chatbot RAG documentation](./12-chatbot-rag/) | LangGraph + FAISS + HuggingFace + Streamlit | Repondre aux questions sur n'importe quel PDF |

### Niveau 3 — Avance (1-2 semaines de livraison client)

| # | Template | Stack | Cas d'usage |
|---|----------|-------|-------------|
| 13 | [Suivi de projet automatise](./13-suivi-projet/) | LangGraph + Supabase + Streamlit | Gerer les taches et generer un resume IA de l'avancement |
| 14 | [Recrutement automatise](./14-recrutement-automatise/) | LangGraph + Supabase + PyMuPDF + Streamlit | Analyser les CVs et gerer le pipeline candidats |
| 15 | [Research & Reporting multi-agents](./15-research-reporting/) | CrewAI + Serper + Streamlit | 4 agents produisent un rapport de marche complet |
| 16 | [Analyse financiere](./16-analyse-financiere/) | LangGraph + Pandas + Streamlit | Calculer les ratios et generer une synthese d'investissement |
| 17 | [Automatisation comptable](./17-automatisation-comptable/) | LangGraph + PyMuPDF + Supabase + Streamlit | Extraire et enregistrer automatiquement les donnees de factures |
| 18 | [Monitoring & Alertes intelligentes](./18-monitoring-alertes/) | LangGraph + Gmail + Supabase + Streamlit | Detecter les anomalies et envoyer des alertes automatiques |
| 19 | [RAG Multi-Sources](./19-rag-multi-sources/) | LangGraph + FAISS + Supabase + Streamlit | Interroger simultanement PDFs, Supabase et APIs externes |
| 20 | [Formation & Quiz Adaptatif](./20-formation-quiz-adaptatif/) | LangGraph + Supabase + Streamlit | Generer des quiz adaptes au niveau et suivre la progression |
| 21 | [Générateur de newsletters](./21-generateur-newsletters/) | LangGraph + Gmail + Supabase + Streamlit | Rédiger et envoyer des newsletters personnalisées |
| 22 | [Agent réseaux sociaux](./22-agent-reseaux-sociaux/) | LangGraph + Serper + Streamlit | Générer des posts et un planning hebdomadaire |
| 23 | [Générateur de devis](./23-generateur-devis/) | LangGraph + FPDF2 + Supabase + Streamlit | Chiffrer un projet et générer un PDF professionnel |

---

## Stack globale

- **Orchestration** : LangGraph, CrewAI
- **LLM** : Anthropic Claude (claude-haiku-4-5-20251001)
- **Base de donnees** : Supabase (PostgreSQL)
- **Recherche semantique** : FAISS, HuggingFace
- **Scraping** : BeautifulSoup, Apify
- **Interface** : Streamlit
- **Email** : Gmail API OAuth2

---

## Utilisation

Chaque template est independant. Pour lancer un template :

```bash
cd XX-nom-template
pip install -r requirements.txt
streamlit run app.py
```

Configurez uniquement `config.py` et `.env` — le code metier ne change pas.

---

## Standards appliques a tous les templates

- `try/except` avec messages d'erreur lisibles
- `invoke_with_retry` (3 tentatives, 5s de delai) pour les erreurs overload Anthropic
- Config centralisee dans `config.py`
- Modele unique : `claude-haiku-4-5-20251001`