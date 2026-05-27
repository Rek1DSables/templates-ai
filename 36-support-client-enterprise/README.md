# 36 — Support Client Enterprise Multi-Agents

Pipeline support client enterprise à 4 agents spécialisés. LangGraph orchestre en séquence : classification du ticket, recherche en base de connaissance, rédaction de la réponse, vérification qualité et décision finale (envoi automatique / escalade / révision). Envoi Gmail optionnel et archivage Supabase.

## Stack

- **LangGraph** — orchestration séquentielle des 4 agents
- **Anthropic Claude** — classification, KB, rédaction, vérification
- **Gmail API** — envoi automatique si décision = envoyer
- **Supabase** — archivage des tickets traités
- **Streamlit** — interface opérateur support

## Fonctionnalités

- Agent A : classification (catégorie, priorité, score complexité 1-10)
- Agent B : recherche solution en base de connaissance interne
- Agent C : rédaction réponse professionnelle et empathique
- Agent D : vérification qualité + décision (envoyer / escalader / revoir)
- Escalade automatique si score complexité >= 8
- Envoi Gmail optionnel si décision = envoyer
- KPIs affichés : ticket ID, catégorie, priorité, complexité, confiance
- Archivage complet dans Supabase
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
36-support-client-enterprise/
├── app.py              # Interface Streamlit + Gmail + Supabase
├── graph.py            # LangGraph 4 agents + router
├── config.py           # Configuration centralisee
├── requirements.txt
├── credentials.json    # OAuth2 Gmail (ne pas committer)
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
GMAIL_SENDER=ton_email@gmail.com
```

## SQL Supabase

```sql
CREATE TABLE tickets_enterprise (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ticket_id TEXT,
    canal TEXT,
    expediteur TEXT,
    sujet TEXT,
    message TEXT,
    categorie TEXT,
    priorite TEXT,
    score_complexite INT,
    reponse_redigee TEXT,
    score_confiance INT,
    decision TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Données de test

- Canal : Email
- Expediteur : client@test.com
- Sujet : Impossible de me connecter depuis ce matin
- Message : Bonjour, depuis ce matin je n'arrive plus a acceder a mon compte. J'ai essaye de reinitialiser mon mot de passe mais je ne recois pas l'email. C'est urgent car j'ai une presentation cet apres-midi.

## Notes

- `credentials.json` à copier depuis un projet Gmail existant
- `SUPABASE_TABLE` = `tickets_enterprise` pour éviter conflit avec template 07
- Supprimer `token.json` et relancer si les scopes Gmail changent

## Modèle utilisé

`claude-haiku-4-5-20251001`