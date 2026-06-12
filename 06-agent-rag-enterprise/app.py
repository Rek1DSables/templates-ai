# app.py
import json
import streamlit as st
from graph import build_graph, VECTOR_STORE, DOCUMENT_REGISTRY
from config import TYPES_DOCUMENTS, NIVEAUX_PERMISSION, PROFILS_UTILISATEUR

# Permissions par profil
PERMISSIONS_PAR_PROFIL = {
    "Employé standard": ["public", "interne"],
    "Manager": ["public", "interne", "confidentiel"],
    "Directeur": ["public", "interne", "confidentiel", "secret"],
    "Administrateur": ["public", "interne", "confidentiel", "secret"],
    "Support client": ["public", "interne"],
    "Commercial": ["public", "interne", "confidentiel"],
    "Juridique": ["public", "interne", "confidentiel", "secret"],
}

# Documents de demo
DOCUMENTS_DEMO = [
    {
        "nom": "Politique de remboursement",
        "type": "Politiques et procédures internes",
        "permission": "public",
        "contenu": """POLITIQUE DE REMBOURSEMENT — Version 2.0 — Janvier 2026

1. CONDITIONS DE REMBOURSEMENT
Tout client peut demander un remboursement dans les 30 jours suivant l'achat si le produit ne correspond pas à la description. Les remboursements sont traités sous 5 jours ouvrés via le moyen de paiement original.

2. PROCESSUS DE DEMANDE
Le client doit contacter le support via support@entreprise.fr avec le numéro de commande et la raison du remboursement. Une confirmation est envoyée sous 24h. Le remboursement est effectif sous 5 jours ouvrés.

3. EXCLUSIONS
Les abonnements annuels ne sont pas remboursables après 30 jours. Les formations consommées à plus de 50% ne sont pas remboursables. Les licences perpétuelles ne sont pas remboursables après activation.

4. CAS PARTICULIERS
En cas de défaut technique prouvé, le remboursement est accordé sans condition de délai. Les clients Enterprise bénéficient d'une politique de remboursement étendue à 90 jours.""",
    },
    {
        "nom": "Grille tarifaire 2026",
        "type": "Rapports financiers",
        "permission": "confidentiel",
        "contenu": """GRILLE TARIFAIRE INTERNE 2026 — CONFIDENTIEL

OFFRE STARTER
Prix : 49€/mois HT
Utilisateurs : jusqu'à 5
Fonctionnalités : CRM basique, emails automatiques, 1 agent IA

OFFRE BUSINESS
Prix : 149€/mois HT
Utilisateurs : jusqu'à 25
Fonctionnalités : CRM avancé, agents IA illimités, intégrations API, support prioritaire

OFFRE ENTERPRISE
Prix : Sur devis (minimum 500€/mois HT)
Utilisateurs : Illimité
Fonctionnalités : Tout Business + déploiement on-premise, SLA 99.9%, account manager dédié

REMISES COMMERCIALES
Engagement annuel : -20%
Volume >10 licences : -15% supplémentaire
Partenaires revendeurs : -30%

OBJECTIFS CA 2026
Q1 : 180k€ | Q2 : 220k€ | Q3 : 280k€ | Q4 : 350k€
ARR cible : 1.2M€""",
    },
    {
        "nom": "Guide technique API",
        "type": "Documentation technique",
        "permission": "interne",
        "contenu": """GUIDE TECHNIQUE API v2.3 — Usage Interne

AUTHENTIFICATION
Toutes les requêtes API nécessitent un header Authorization: Bearer {token}.
Les tokens expirent après 24h. Renouvellement via POST /auth/refresh.

ENDPOINTS PRINCIPAUX
GET /api/v2/leads — Liste les leads avec pagination (max 100/page)
POST /api/v2/leads — Crée un lead (champs requis: email, source)
PUT /api/v2/leads/{id} — Met à jour un lead
DELETE /api/v2/leads/{id} — Supprime un lead (soft delete)

WEBHOOKS
Configuration via dashboard Settings > Webhooks.
Events disponibles: lead.created, lead.qualified, lead.converted
Retry automatique: 3 tentatives avec backoff exponentiel (1min, 5min, 30min)

LIMITES
Rate limit: 1000 req/min pour les plans Business+
Payload max: 10MB par requête
Timeout: 30 secondes

CODES D'ERREUR
400: Données invalides | 401: Non authentifié | 403: Droits insuffisants
404: Ressource inexistante | 429: Rate limit dépassé | 500: Erreur serveur""",
    },
    {
        "nom": "Procédure onboarding client",
        "type": "Politiques et procédures internes",
        "permission": "interne",
        "contenu": """PROCÉDURE ONBOARDING CLIENT — SOP-OB-001

ÉTAPE 1 — J0 : Signature contrat
Envoyer email de bienvenue avec accès plateforme sous 2h.
Créer le compte dans le CRM avec segment approprié.
Assigner un Customer Success Manager.

ÉTAPE 2 — J1 : Appel de lancement
Durée : 45 minutes. Participants : CSM + décideur client.
Objectifs : comprendre les cas d'usage prioritaires, configurer les intégrations essentielles.
Livrable : plan d'action 30 jours partagé dans Notion.

ÉTAPE 3 — J7 : Vérification adoption
Analyser les métriques d'usage dans le dashboard.
Si usage < 30% des fonctionnalités clés : déclencher session de formation.
Objectif : first value dans les 7 premiers jours.

ÉTAPE 4 — J30 : Business Review
Bilan des 30 premiers jours avec le client.
Présenter ROI réalisé vs objectifs fixés.
Identifier les opportunités d'expansion.

CRITÈRES DE SUCCÈS
NPS > 8 à J30 | Adoption > 70% des fonctionnalités clés | 0 ticket critique non résolu""",
    },
]


st.set_page_config(page_title="Agent RAG Enterprise", page_icon="🧬", layout="centered")
st.title("🧬 Agent RAG Enterprise")
st.caption("Base de connaissance privée avec gouvernance, permissions, anti-hallucination et audit trail")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés :**
1. **Agent Indexation** — chunking stratégique + embeddings + registre documents
2. **Agent Retrieval & Gouvernance** — similarité vectorielle + filtrage permissions
3. **Agent Génération** — réponse ancrée strictement dans les sources avec citations
4. **Agent Anti-Hallucination** — vérifie l'ancrage de la réponse dans les sources
    """)

# Sidebar — configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    profil = st.selectbox("Profil utilisateur", PROFILS_UTILISATEUR)
    permissions = PERMISSIONS_PAR_PROFIL.get(profil, ["public", "interne"])

    st.markdown("**Permissions actives :**")
    for p in permissions:
        st.markdown(NIVEAUX_PERMISSION.get(p, p))

    st.divider()
    st.markdown(f"**Documents indexés :** {len(DOCUMENT_REGISTRY)}")
    st.markdown(f"**Fragments en mémoire :** {len(VECTOR_STORE)}")

st.divider()

# Onglets principaux
tab_index, tab_query = st.tabs(["📁 Indexer des documents", "💬 Interroger la base"])

with tab_index:
    st.subheader("Indexer des documents")

    source_docs = st.radio("Source", ["Documents de démo", "Ajouter un document"], horizontal=True)

    if source_docs == "Documents de démo":
        st.info("4 documents de démo prêts à indexer (Public, Confidentiel, Interne x2)")
        for doc in DOCUMENTS_DEMO:
            perm = doc["permission"]
            icone = "🟢" if perm == "public" else "🟡" if perm == "interne" else "🟠"
            st.markdown(f"{icone} **{doc['nom']}** — {doc['type']} — {perm.capitalize()}")

        if st.button("Indexer les documents de démo", use_container_width=True):
            with st.spinner("Indexation en cours..."):
                graph = build_graph()
                result = graph.invoke({
                    "mode": "indexer",
                    "documents_a_indexer": DOCUMENTS_DEMO,
                    "documents_indexes": [],
                    "question": "",
                    "profil_utilisateur": profil,
                    "permissions_utilisateur": permissions,
                    "chunks_retrouves": [],
                    "chunks_autorises": [],
                    "contexte_assemble": "",
                    "reponse": "",
                    "sources_citees": [],
                    "score_confiance": 0.0,
                    "hallucination_detectee": False,
                    "avertissement": "",
                    "audit_log": [],
                    "erreur": "",
                })

            if result["erreur"]:
                st.error(result["erreur"])
            else:
                st.success(f"✅ {len(result['documents_indexes'])} documents indexés — {len(VECTOR_STORE)} fragments en mémoire")
                for doc in result["documents_indexes"]:
                    st.markdown(f"- **{doc['nom']}** — {doc['nb_chunks']} fragments — {doc['permission'].capitalize()}")

    else:
        nom = st.text_input("Nom du document", placeholder="Manuel utilisateur v3")
        type_doc = st.selectbox("Type", TYPES_DOCUMENTS)
        permission = st.selectbox("Niveau de permission", list(NIVEAUX_PERMISSION.keys()),
            format_func=lambda x: NIVEAUX_PERMISSION[x])
        contenu = st.text_area("Contenu du document", height=200,
            placeholder="Colle ici le contenu du document...")

        if st.button("Indexer ce document", use_container_width=True):
            if not nom or not contenu:
                st.error("Merci de renseigner le nom et le contenu.")
            else:
                with st.spinner("Indexation..."):
                    graph = build_graph()
                    result = graph.invoke({
                        "mode": "indexer",
                        "documents_a_indexer": [{"nom": nom, "type": type_doc, "permission": permission, "contenu": contenu}],
                        "documents_indexes": [],
                        "question": "",
                        "profil_utilisateur": profil,
                        "permissions_utilisateur": permissions,
                        "chunks_retrouves": [],
                        "chunks_autorises": [],
                        "contexte_assemble": "",
                        "reponse": "",
                        "sources_citees": [],
                        "score_confiance": 0.0,
                        "hallucination_detectee": False,
                        "avertissement": "",
                        "audit_log": [],
                        "erreur": "",
                    })
                if result["erreur"]:
                    st.error(result["erreur"])
                else:
                    st.success(f"✅ Document indexé — {len(VECTOR_STORE)} fragments total")

with tab_query:
    st.subheader("Interroger la base de connaissance")

    if not VECTOR_STORE:
        st.warning("Aucun document indexé. Indexez d'abord des documents dans l'onglet précédent.")
    else:
        question = st.text_input(
            "Votre question",
            placeholder="Quelle est la politique de remboursement pour les abonnements annuels ?"
        )

        exemples = [
            "Quelle est la politique de remboursement ?",
            "Quel est le prix de l'offre Enterprise ?",
            "Comment configurer les webhooks API ?",
            "Quelles sont les étapes de l'onboarding client ?",
            "Quel est l'objectif de CA au Q4 2026 ?",
            "Quelle est la procédure de recrutement pour un poste de directeur financier ?",
        ]
        exemple = st.selectbox("Exemples de questions", [""] + exemples)
        if exemple and not question:
            question = exemple

        if st.button("Interroger", use_container_width=True, disabled=not question):
            with st.spinner("Recherche et génération en cours..."):
                graph = build_graph()
                result = graph.invoke({
                    "mode": "interroger",
                    "documents_a_indexer": [],
                    "documents_indexes": [],
                    "question": question,
                    "profil_utilisateur": profil,
                    "permissions_utilisateur": permissions,
                    "chunks_retrouves": [],
                    "chunks_autorises": [],
                    "contexte_assemble": "",
                    "reponse": "",
                    "sources_citees": [],
                    "score_confiance": 0.0,
                    "hallucination_detectee": False,
                    "avertissement": "",
                    "audit_log": [],
                    "erreur": "",
                })

            if result["erreur"]:
                st.error(result["erreur"])
                st.stop()

            # Alertes
            if result["hallucination_detectee"]:
                st.error("🚨 Hallucination potentielle détectée — vérifier manuellement")
            if result["avertissement"]:
                st.warning(result["avertissement"])

            # Métriques
            score = result["score_confiance"]
            icone_confiance = "🟢" if score >= 0.7 else "🟡" if score >= 0.4 else "🔴"
            col1, col2, col3 = st.columns(3)
            col1.metric("Confiance", f"{icone_confiance} {score:.0%}")
            col2.metric("Sources utilisées", len(result["sources_citees"]))
            col3.metric("fragments analysés", len(result["chunks_retrouves"]))

            st.divider()

            # Réponse
            st.markdown("**Réponse**")
            st.markdown(result["reponse"])

            # Sources
            if result["sources_citees"]:
                st.divider()
                st.markdown("**Sources citées**")
                for s in result["sources_citees"]:
                    perm = s.get("permission", "interne")
                    icone = "🟢" if perm == "public" else "🟡" if perm == "interne" else "🟠"
                    st.markdown(f"{icone} **{s['nom']}** — {s['type']} — Score : {s['score_max']:.0%}")

            # Audit trail
            with st.expander("📋 Audit Trail"):
                for entry in result["audit_log"]:
                    detail = entry.get("detail", "")
                    suffix = f" | {detail}" if detail else ""
                    st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')}{suffix}")

                st.download_button(
                    label="📦 Télécharger Audit Trail JSON",
                    data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
                    file_name="audit_rag.json",
                    mime="application/json",
                )