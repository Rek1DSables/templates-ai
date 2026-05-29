# 02 — Agent EU AI Act Compliance

Pipeline d'audit de conformité EU AI Act (Règlement 2024/1689). LangGraph orchestre 5 nœuds : classification du système, analyse par article, plan de remédiation en 2 parties, verdict final. Audit trail complet conforme aux exigences réglementaires. Export PDF et JSON.

## Stack

- **LangGraph** — orchestration séquentielle 5 nœuds
- **Anthropic Claude Sonnet** — analyse juridique et plan de remédiation
- **Anthropic Claude Haiku** — classification et analyse par article
- **FPDF2** — export PDF rapport complet
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Classification automatique du niveau de risque (Inacceptable / Élevé / Limité / Minimal)
- Détection des pratiques interdites (Article 5)
- Analyse de conformité par article applicable (6, 9, 10, 13, 14, 15, 17, 72)
- Détection des flags critiques (discrimination, droits fondamentaux, opacité, GPAI)
- Score de conformité global 0-100
- Plan de remédiation 90 jours avec responsables et délais
- Checklist de conformité en 15 points
- Audit trail complet horodaté (conforme Article 17 EU AI Act)
- Export PDF rapport complet + JSON audit trail
- Bandeau deadlines EU AI Act 2025-2027
- Retry automatique (3 tentatives, 5s)

## Deadlines EU AI Act

| Date | Obligation |
|------|-----------|
| Février 2025 | Pratiques interdites (Article 5) — EN VIGUEUR |
| Août 2025 | Obligations GPAI — EN VIGUEUR |
| **Août 2026** | **Systèmes à haut risque Annexe III — DEADLINE** |
| Août 2027 | Systèmes embarqués existants |

## Structure

```
02-agent-eu-ai-act-compliance/
├── app.py          # Interface Streamlit + audit trail
├── graph.py        # LangGraph 5 nœuds
├── config.py       # Articles EU AI Act, niveaux risque, deadlines
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

## Données de test

- Nom : RecrutAI Pro
- Secteur : RH / Recrutement
- Catégorie : Emploi et gestion des travailleurs
- Données : CV, profils LinkedIn, données biographiques, scores IA
- Description : Système de scoring automatique de CV pour présélection candidats
- Résultat attendu : Niveau risque ÉLEVÉ, 7 flags critiques, score ~40-60/100

## Modèles utilisés

- `claude-haiku-4-5-20251001` — classification et analyse articles
- `claude-sonnet-4-6` — plan de remédiation et verdict final