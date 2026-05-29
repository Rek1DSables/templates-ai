# 07 — Agent Analyse Documentaire Avancée

Pipeline multi-agents d'analyse de documents juridiques et financiers complexes. 4 agents spécialisés en séquence : extraction structurée par axe, vérification des risques, synthèse executive, matrice des risques et recommandations. Export PDF avec audit trail.

## Stack

- **LangGraph** — orchestration séquentielle 4 agents
- **Anthropic Claude Sonnet** — synthèse et recommandations
- **Anthropic Claude Haiku** — extraction structurée et identification risques
- **PyMuPDF** — extraction texte depuis PDF uploadé
- **FPDF2** — export PDF rapport complet
- **Streamlit** — interface utilisateur

## Architecture des agents

| Agent | Rôle |
|-------|------|
| Agent Extraction | Extrait les données pour chaque axe d'analyse |
| Agent Vérification Risques | Identifie risques, incohérences, éléments manquants |
| Agent Synthèse Partie 1 | Executive summary + informations extraites |
| Agent Synthèse Partie 2 | Matrice risques + recommandations + verdict |

## Fonctionnalités

- 10 types de documents : contrat commercial, bail, RFP, due diligence, NDA, CGV, audit, contrat travail, partenariat
- Axes d'analyse configurés par type de document (8-9 axes par type)
- Extraction structurée avec score de fiabilité et localisation dans le document
- Matrice des risques par niveau (critique / élevé / moyen / faible)
- Score de risque global 0-100
- Verdict : signer / négocier / ne pas signer
- 5 recommandations prioritaires avec responsable et délai
- Upload PDF ou saisie texte
- Document de démo inclus (contrat commercial avec clauses abusives)
- Export PDF rapport complet + audit trail JSON
- Retry automatique (3 tentatives, 5s)

## Ce qui différencie ce template d'un simple prompt LLM

- **Pipeline multi-agents** — extraction → vérification → synthèse en séquence
- **Axes configurés par type** — pas un prompt générique mais une analyse structurée métier
- **Détection de clauses abusives** — délai de paiement illégal, responsabilité illimitée, résiliation asymétrique
- **Audit trail** — chaque extraction tracée avec fiabilité

## Structure

```
07-agent-analyse-documentaire/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph 4 agents
├── config.py       # Types documents, axes d'analyse
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
```

## Document de test inclus

Contrat commercial TECHCORP-DEVAGENCY avec 4 clauses abusives intentionnelles :
- Délai de paiement illégal (90 jours vs max 60 jours légal)
- Responsabilité illimitée du prestataire
- Résiliation asymétrique (Client sans préavis, Prestataire 6 mois)
- Cession de propriété intellectuelle des outils génériques

## Modèles utilisés

- `claude-haiku-4-5-20251001` — extraction structurée et risques
- `claude-sonnet-4-6` — synthèse et recommandations