# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Database
DB_TYPE = os.getenv("DB_TYPE", "sqlite")  # sqlite | postgresql | supabase
DB_URL = os.getenv("DB_URL", "demo.db")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Types de questions supportées
EXEMPLES_QUESTIONS = [
    "Quel est le chiffre d'affaires total par région ?",
    "Quels sont les 5 produits les plus vendus ce mois ?",
    "Quelle est la tendance du CA sur les 6 derniers mois ?",
    "Quel commercial a le meilleur taux de conversion ?",
    "Quelles sont les anomalies dans les ventes de mai ?",
    "Compare les performances Q1 vs Q2 par catégorie de produit",
    "Quel est le panier moyen par segment client ?",
    "Identifie les clients à risque de churn",
]

# Schéma demo (SQLite)
SQL_DEMO_SCHEMA = """
CREATE TABLE IF NOT EXISTS ventes (
    id INTEGER PRIMARY KEY,
    date TEXT,
    produit TEXT,
    categorie TEXT,
    region TEXT,
    commercial TEXT,
    client TEXT,
    segment TEXT,
    quantite INTEGER,
    prix_unitaire REAL,
    ca REAL,
    marge REAL
);

CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY,
    email TEXT,
    entreprise TEXT,
    segment TEXT,
    region TEXT,
    ca_total REAL,
    nb_commandes INTEGER,
    derniere_commande TEXT,
    statut TEXT
);
"""

SQL_DEMO_DATA = """
INSERT OR IGNORE INTO ventes VALUES
(1,'2026-01-05','CRM Pro','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',2,450,900,360),
(2,'2026-01-12','ERP Cloud','SaaS','Lyon','Bob Dupont','Beta SA','PME',1,1200,1200,480),
(3,'2026-01-18','IA Automation','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',3,800,2400,960),
(4,'2026-01-25','Consulting IA','Service','Paris','Alice Martin','Eta SA','ETI',2,1500,3000,900),
(5,'2026-02-03','CRM Pro','SaaS','Bordeaux','Clara Simon','Delta Inc','PME',4,450,1800,720),
(6,'2026-02-10','IA Automation','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',2,800,1600,640),
(7,'2026-02-18','ERP Cloud','SaaS','Lyon','Bob Dupont','Beta SA','PME',2,1200,2400,960),
(8,'2026-02-25','Consulting IA','Service','Bordeaux','Clara Simon','Delta Inc','PME',1,1500,1500,450),
(9,'2026-03-05','CRM Pro','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',5,450,2250,900),
(10,'2026-03-12','IA Automation','SaaS','Lyon','Bob Dupont','Zeta Corp','ETI',3,800,2400,960),
(11,'2026-03-20','ERP Cloud','SaaS','Marseille','David Roux','Epsilon SA','ETI',2,1200,2400,960),
(12,'2026-03-28','Consulting IA','Service','Paris','Alice Martin','Gamma SARL','PME',2,1500,3000,900),
(13,'2026-04-05','CRM Pro','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',3,450,1350,540),
(14,'2026-04-12','IA Automation','SaaS','Bordeaux','Clara Simon','Delta Inc','PME',2,800,1600,640),
(15,'2026-04-20','ERP Cloud','SaaS','Lyon','Bob Dupont','Beta SA','PME',1,1200,1200,480),
(16,'2026-04-28','Consulting IA','Service','Paris','Alice Martin','Eta SA','ETI',3,1500,4500,1350),
(17,'2026-05-05','CRM Pro','SaaS','Marseille','David Roux','Epsilon SA','ETI',2,450,900,360),
(18,'2026-05-12','IA Automation','SaaS','Paris','Alice Martin','Acme Corp','Enterprise',4,800,3200,1280),
(19,'2026-05-20','ERP Cloud','SaaS','Bordeaux','Clara Simon','Delta Inc','PME',2,1200,2400,960),
(20,'2026-05-28','Consulting IA','Service','Paris','Alice Martin','Gamma SARL','PME',1,1500,1500,450);

INSERT OR IGNORE INTO clients VALUES
(1,'acme@acme.com','Acme Corp','Enterprise','Paris',12600,6,'2026-05-18','actif'),
(2,'beta@beta.com','Beta SA','PME','Lyon',5280,4,'2026-04-15','actif'),
(3,'delta@delta.com','Delta Inc','PME','Bordeaux',4900,4,'2026-05-20','actif'),
(4,'eta@eta.com','Eta SA','ETI','Paris',7500,3,'2026-04-28','actif'),
(5,'gamma@gamma.com','Gamma SARL','PME','Paris',4500,2,'2026-05-28','actif'),
(6,'epsilon@epsilon.com','Epsilon SA','ETI','Marseille',3300,2,'2026-05-05','a_risque'),
(7,'zeta@zeta.com','Zeta Corp','ETI','Lyon',2400,1,'2026-03-10','a_risque');
"""