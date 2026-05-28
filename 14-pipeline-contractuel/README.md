# 29 — Générateur de Contrats AI

Pipeline de génération automatique de contrats freelance professionnels via LangGraph et Claude. L'utilisateur remplit un formulaire, Claude rédige le contrat structuré, FPDF2 produit le PDF téléchargeable, Supabase archive chaque contrat généré.

## Stack

- **LangGraph** — orchestration du pipeline de génération
- **Anthropic Claude** — rédaction juridique du contrat
- **FPDF2** — génération du fichier PDF
- **Supabase** — stockage des contrats générés
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Sélection du type de contrat (prestation, conseil, développement, mission freelance)
- Formulaire prestataire + client + mission en une seule page
- Génération Claude avec 10 articles juridiques structurés (objet, durée, tarif, obligations, confidentialité, propriété intellectuelle, résiliation, litiges)
- Export PDF téléchargeable directement depuis l'interface
- Archivage automatique dans Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
29-generateur-contrats/
├── app.py            # Interface Streamlit + génération PDF
├── graph.py          # LangGraph + appel Claude
├── config.py         # Configuration centralisée
├── requirements.txt  # Dépendances
├── .env              # Variables d'environnement
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

## SQL Supabase

```sql
CREATE TABLE contrats (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    type_contrat TEXT,
    freelance_nom TEXT,
    client_nom TEXT,
    prestation TEXT,
    tarif TEXT,
    duree TEXT,
    date_debut TEXT,
    contenu TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Type : Prestation de services
- Prestataire : Jean Martin / jean@freelance.fr
- Client : Acme Corp / contact@acme.com
- Prestation : Développement d'un chatbot AI pour le service client
- Tarif : 600€ HT/jour
- Durée : 2 mois
- Date de début : 01/06/2026

## Modèle utilisé

`claude-haiku-4-5-20251001`