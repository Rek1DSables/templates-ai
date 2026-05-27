# 24 — Générateur de Propositions Commerciales AI

Pipeline de génération de propositions commerciales complètes. LangGraph orchestre 3 agents en séquence : analyse du besoin client, construction de la solution technique, rédaction de la propale complète avec planning, budget et CGV. Export PDF inclus.

## Stack

- **LangGraph** — orchestration séquentielle des 3 agents
- **Anthropic Claude** — analyse besoin, solution, rédaction propale
- **Supabase** — archivage des propositions
- **FPDF2** — export PDF professionnel
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Formulaire prestataire + client + mission en une page
- Analyse des enjeux business et facteurs clés de succès
- Construction de la solution technique avec livrables et planning
- Proposition commerciale complète 7 sections (contexte, solution, livrables, investissement, pourquoi nous, prochaines étapes, CGV)
- Modalités de paiement et ROI calculé automatiquement
- Export PDF téléchargeable
- Archivage Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
24-generateur-propales/
├── app.py          # Interface Streamlit + export PDF
├── graph.py        # LangGraph 3 agents
├── config.py       # Configuration centralisee
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

## SQL Supabase

```sql
CREATE TABLE propales (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    prestataire_nom TEXT,
    client_nom TEXT,
    client_entreprise TEXT,
    type_mission TEXT,
    budget TEXT,
    delai TEXT,
    mode_facturation TEXT,
    propale TEXT,
    date_propale TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Prestataire : Jean Martin / jean@freelance.fr / Expert AI Automation LangGraph Claude API
- Client : Marie Dupont / Acme Corp / E-commerce
- Mission : Developpement AI / Agents / Forfait / 8 000 EUR / 6 semaines
- Besoin : Automatiser la qualification de leads entrants, 50 leads/semaine traites manuellement
- Objectifs : Reduire le temps de qualification de 4h a 30min/semaine

## Notes

- Propale longue : upgrade Sonnet prevu sur `rediger_propale` en passe polish

## Modèle utilisé

`claude-haiku-4-5-20251001`