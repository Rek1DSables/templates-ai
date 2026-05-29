# 10 — Agent Pipeline Contractuel Multi-Agents

Pipeline multi-agents de traitement contractuel complet. 4 agents spécialisés : extraction et structuration des clauses, analyse des risques juridiques, synthèse avec verdict, génération d'un contrat amélioré ou nouveau. 3 modes : analyse, génération, analyse + amélioration.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — synthèse et génération contrat
- **Anthropic Claude Haiku** — extraction clauses et analyse risques
- **Supabase** — persistance des contrats traités
- **PyMuPDF** — extraction texte depuis PDF
- **FPDF2** — export PDF rapport + contrat
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Extraction | Extrait et structure toutes les clauses contractuelles |
| Agent Analyse Risques | Identifie risques, clauses abusives, illégalités |
| Agent Synthèse | Verdict, recommandations, actions avant signature |
| Agent Génération | Contrat amélioré ou nouveau contrat conforme |

## Fonctionnalités

- 3 modes : Analyser / Générer / Analyser + Améliorer
- 8 types de contrats supportés
- Détection automatique des clauses obligatoires manquantes
- Matrice des risques par niveau (critique / élevé / moyen / faible)
- Score de risque global 0-100
- Détection de clauses abusives et illégalités (ex: délai paiement > 60j LME)
- Génération de contrat amélioré avec corrections des risques identifiés
- Upload PDF ou saisie texte
- Document de démo inclus avec clauses abusives intentionnelles
- Persistance dans Supabase
- Export PDF rapport complet + audit trail JSON
- Retry automatique (3 tentatives, 5s)

## Structure

```
10-agent-pipeline-contractuel-multi-agents/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph 4 agents
├── config.py       # Types contrats, clauses obligatoires
├── requirements.txt
├── .env
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Variables d'environnement

```
ANTHROPIC_API_KEY=ta_clé_ici
SUPABASE_URL=ton_url_supabase
SUPABASE_KEY=ta_clé_supabase
```

## Document de test inclus

Contrat INNOVATECH-DEVPRO avec 4 anomalies intentionnelles :
- Délai paiement 90j (illégal — max 60j LME)
- Responsabilité illimitée du prestataire
- Résiliation asymétrique (6 mois prestataire vs 0 client)
- Cession PI des outils propriétaires du prestataire

## Modèles utilisés

- `claude-haiku-4-5-20251001` — extraction et risques
- `claude-sonnet-4-6` — synthèse et génération