# 30 — Pipeline Onboarding Employé AI

Pipeline RH automatisé pour générer le kit d'accueil complet d'un nouvel employé. LangGraph orchestre 3 agents Claude en séquence : email de bienvenue, checklist d'onboarding et liste des accès à provisionner. Envoi Gmail intégré et archivage Supabase.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — génération email, checklist et liste d'accès
- **Gmail API** — envoi automatique de l'email de bienvenue
- **Supabase** — archivage des dossiers d'onboarding
- **Streamlit** — interface RH

## Fonctionnalités

- Formulaire RH complet (employé, poste, département, manager, date d'arrivée)
- Génération simultanée de 3 documents via 3 nœuds LangGraph en séquence
- Email de bienvenue personnalisé avec objet extrait automatiquement
- Checklist onboarding structurée en 4 phases (avant arrivée, jour J, semaine 1, mois 1)
- Liste d'accès et outils à provisionner selon le poste et département
- Envoi Gmail OAuth2 optionnel depuis l'interface
- Archivage complet du dossier dans Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
30-onboarding-employe/
├── app.py              # Interface Streamlit + Gmail + Supabase
├── graph.py            # LangGraph 3 noeuds sequentiels
├── config.py           # Configuration centralisee
├── requirements.txt    # Dependances
├── credentials.json    # OAuth2 Gmail (ne pas committer)
├── .env                # Variables d'environnement
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
GMAIL_SENDER=ton_email@gmail.com
```

## SQL Supabase

```sql
CREATE TABLE onboarding (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prenom TEXT,
    nom TEXT,
    poste TEXT,
    departement TEXT,
    manager TEXT,
    date_arrivee TEXT,
    email_employe TEXT,
    email_bienvenue TEXT,
    checklist TEXT,
    acces TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Prénom : Marie / Nom : Dupont
- Poste : Développeur Backend / Département : Tech
- Manager : Jean Martin
- Date d'arrivée : 01/06/2026
- Email : marie.dupont@test.com
- Gmail : décoché pour le premier test

## Notes

- `credentials.json` à copier depuis un projet Gmail existant
- Supprimer `token.json` et relancer si les scopes Gmail changent
- Run without RLS sur la table Supabase en phase de test

## Modèle utilisé

`claude-haiku-4-5-20251001`