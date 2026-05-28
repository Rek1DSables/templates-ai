# 07 — Agent Finance & Documents

Pipeline d'analyse et de génération de documents financiers. LangGraph orchestre 3 nœuds : extraction structurée des données, détection d'anomalies comptables, génération de devis et factures conformes au droit français. Export PDF et JSON inclus.

## Stack

- **LangGraph** — orchestration avec routeur conditionnel
- **Anthropic Claude** — extraction JSON, détection anomalies, génération documents
- **FPDF2** — export PDF
- **PyMuPDF** — extraction texte depuis PDF uploadé
- **Streamlit** — interface utilisateur

## Fonctionnalités

- **Mode Analyse** : upload PDF ou saisie texte → extraction structurée (émetteur, destinataire, lignes, montants) → détection d'anomalies (erreurs de calcul, mentions manquantes, délais illégaux) → export PDF + JSON
- **Mode Génération** : formulaire → devis ou facture générés avec mentions légales → export PDF + JSON
- 7 types de documents supportés (Facture, Devis, Avoir, Bon de commande...)
- Taux de TVA configurables (0%, 5.5%, 10%, 20%)
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
07-agent-finance-documents/
├── app.py          # Interface Streamlit + export PDF/JSON
├── graph.py        # LangGraph 3 nœuds + routeur conditionnel
├── config.py       # Configuration centralisée
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

```
FACTURE N° FAC-2024-0042
Date : 15 mars 2024 — Échéance : 15 avril 2024

ÉMETTEUR :
Dupont Informatique SARL
SIRET : 123 456 789 00012
12 rue de la Paix, 75001 Paris

DESTINATAIRE :
Acme Corp — SIRET : 987 654 321 00015
45 avenue Montaigne, 75008 Paris

PRESTATIONS :
- Maintenance informatique : 1 x 750,00 EUR HT (TVA 20%)
- Abonnement CRM Mars 2024 : 1 x 750,00 EUR HT (TVA 20%)

TOTAL HT : 1 500,00 EUR | TVA : 300,00 EUR | TOTAL TTC : 1 800,00 EUR
```

## Modèle utilisé

`claude-haiku-4-5-20251001`