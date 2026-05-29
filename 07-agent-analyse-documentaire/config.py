# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"
MODEL_SONNET = "claude-sonnet-4-6"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Types de documents supportés
TYPES_DOCUMENTS = [
    "Contrat commercial",
    "Bail immobilier",
    "Appel d'offres / RFP",
    "Due diligence financière",
    "Accord de confidentialité (NDA)",
    "Conditions générales de vente",
    "Rapport d'audit",
    "Contrat de travail",
    "Accord de partenariat",
    "Autre document juridique",
]

# Axes d'extraction par type
AXES_PAR_TYPE = {
    "Contrat commercial": [
        "Parties contractantes et représentants légaux",
        "Objet et périmètre du contrat",
        "Durée et conditions de renouvellement",
        "Conditions financières et modalités de paiement",
        "Clauses de responsabilité et limitations",
        "Conditions de résiliation",
        "Propriété intellectuelle",
        "Loi applicable et juridiction",
        "Clauses abusives ou déséquilibrées",
    ],
    "Bail immobilier": [
        "Parties (bailleur et preneur)",
        "Bien loué et surface",
        "Durée du bail et renouvellement",
        "Loyer et charges refacturables",
        "Dépôt de garantie",
        "Clause de solidarité",
        "Destination des locaux",
        "Travaux et état des lieux",
        "Clauses résolutoires",
    ],
    "Appel d'offres / RFP": [
        "Entité émettrice et contexte",
        "Périmètre de la prestation",
        "Critères de sélection explicites",
        "Critères cachés ou implicites",
        "Budget et conditions financières",
        "Délais et planning",
        "Exigences techniques et certifications",
        "Conditions de soumission",
        "Points de vigilance et risques",
    ],
    "Due diligence financière": [
        "Entité auditée et périmètre",
        "Indicateurs financiers clés",
        "Anomalies et red flags",
        "Engagements hors bilan",
        "Litiges et provisions",
        "Qualité des actifs",
        "Dette et structure de financement",
        "Risques identifiés",
    ],
    "Accord de confidentialité (NDA)": [
        "Parties et représentants",
        "Définition des informations confidentielles",
        "Durée de confidentialité",
        "Exclusions",
        "Obligations des parties",
        "Sanctions en cas de violation",
        "Loi applicable",
    ],
}

# Niveaux de risque
NIVEAUX_RISQUE = {
    "critique": "🔴",
    "eleve": "🟠",
    "moyen": "🟡",
    "faible": "🟢",
}

# Recommandations par défaut
AXES_DEFAUT = [
    "Parties contractantes",
    "Objet du document",
    "Durée et dates clés",
    "Conditions financières",
    "Clauses de risque",
    "Points de vigilance",
]