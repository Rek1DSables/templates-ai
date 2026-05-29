# app.py
import json
import streamlit as st
from graph import build_graph
from config import CATEGORIES_WORKFLOW, PRIORITES, SQL_SETUP


EMAILS_DEMO = [
    {
        "expediteur": "sophie.martin@techcorp.fr",
        "sujet": "URGENT — Impossible d'accéder à la plateforme depuis ce matin",
        "corps": "Bonjour, depuis 8h ce matin toute mon équipe est bloquée. Nous avons une démo client à 14h et c'est absolument critique. Message d'erreur : 'Service unavailable 503'. Nous avons 50 utilisateurs actifs et ce blocage nous coûte énormément. Merci de traiter en urgence absolue.",
        "date": "2026-05-29 09:15",
    },
    {
        "expediteur": "jean.dupont@startup-ia.com",
        "sujet": "Demande de démo et tarifs — équipe de 30 personnes",
        "corps": "Bonjour, nous sommes une startup IA en série A (30 personnes). Nous cherchons une solution d'automatisation pour notre équipe commerciale. Pourriez-vous nous présenter votre offre et nous envoyer une proposition tarifaire ? Nous avons un budget d'environ 3000€/mois.",
        "date": "2026-05-29 10:30",
    },
    {
        "expediteur": "direction@cabinet-juridique.fr",
        "sujet": "RÉCLAMATION FORMELLE — Double facturation mai 2026",
        "corps": "Bonjour, j'ai constaté une double facturation sur ma carte bancaire pour le mois de mai 2026, soit 2x 890€. Je vous mets en demeure de procéder au remboursement sous 48h. Sans retour de votre part, je saisirai ma banque et le médiateur de la consommation.",
        "date": "2026-05-29 11:00",
    },
    {
        "expediteur": "noreply@promo-flash.com",
        "sujet": "🎉 Offre exceptionnelle -80% aujourd'hui seulement!!!",
        "corps": "Cliquez ici pour profiter de notre offre exclusive. Produits premium à prix cassés. Livraison gratuite. Offre valable 24h seulement. Ne ratez pas cette opportunité unique.",
        "date": "2026-05-29 11:45",
    },
]


st.set_page_config(page_title="Agent Workflow Métier E2E", page_icon="⚙️", layout="centered")
st.title("⚙️ Agent Workflow Métier E2E")
st.caption("Pipeline multi-agents : Email → CRM Lookup → Classification → Ticket → Réponse → Gmail")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**5 agents spécialisés en séquence :**
1. **Agent CRM Lookup** — recherche le contact, récupère l'historique
2. **Agent Classification** — catégorie, priorité, sentiment, entités extraites
3. **Agent CRM Update** — crée le ticket, met à jour le contact, programme la relance
4. **Agent Réponse** — génère la réponse contextualisée avec numéro de ticket
5. **Agent Gmail** — envoie la réponse (mode réel) ou simule (mode démo)
    """)

with st.expander("🗄️ Setup Supabase — SQL à exécuter"):
    st.code(SQL_SETUP, language="sql")

st.divider()

mode_demo = st.toggle("Mode démo (emails fictifs, pas d'envoi réel)", value=True)

if mode_demo:
    st.subheader("Sélectionner un email de test")
    email_choisi = st.selectbox(
        "Email",
        range(len(EMAILS_DEMO)),
        format_func=lambda i: f"{EMAILS_DEMO[i]['expediteur']} — {EMAILS_DEMO[i]['sujet'][:50]}..."
    )
    email = EMAILS_DEMO[email_choisi]
    expediteur = email["expediteur"]
    sujet = email["sujet"]
    corps = email["corps"]
    date = email["date"]

    with st.container(border=True):
        st.markdown(f"**De :** {expediteur}")
        st.markdown(f"**Sujet :** {sujet}")
        st.markdown(f"**Date :** {date}")
        st.markdown(f"**Corps :** {corps[:200]}...")
else:
    st.subheader("Email entrant")
    expediteur = st.text_input("Expéditeur", placeholder="contact@client.com")
    sujet = st.text_input("Sujet", placeholder="Objet de l'email")
    date = st.text_input("Date", value="2026-05-29 09:00")
    corps = st.text_area("Corps de l'email", height=150, placeholder="Contenu de l'email...")

if st.button("Traiter l'email", use_container_width=True):
    if not expediteur or not corps:
        st.error("Merci de renseigner l'expéditeur et le corps de l'email.")
    else:
        with st.spinner("Pipeline en cours — 5 agents..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "email_expediteur": expediteur,
                    "email_sujet": sujet,
                    "email_corps": corps,
                    "email_date": date,
                    "mode_demo": mode_demo,
                    "contact_connu": False,
                    "contact_data": {},
                    "historique_interactions": [],
                    "categorie": "",
                    "priorite": "",
                    "sentiment": "",
                    "resume": "",
                    "entites_extraites": {},
                    "ticket_reference": "",
                    "equipe_assignee": "",
                    "sla_heures": 24,
                    "reponse_generee": "",
                    "relance_programmee": "",
                    "actions_executees": [],
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        priorite = result["priorite"]
        icone = PRIORITES.get(priorite, {}).get("label", priorite)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Catégorie", result["categorie"].split(" — ")[0] if result["categorie"] else "—")
        col2.metric("Priorité", icone)
        col3.metric("Ticket", result["ticket_reference"] or "—")
        col4.metric("Équipe", result["equipe_assignee"].replace("equipe_", "").capitalize() if result["equipe_assignee"] else "—")

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Analyse & Actions",
            "Réponse générée",
            "Audit Trail",
            "Données CRM",
        ])

        with tab1:
            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown("**Classification**")
                st.markdown(f"Catégorie : **{result['categorie']}**")
                st.markdown(f"Priorité : **{icone}**")
                st.markdown(f"Sentiment : **{result['sentiment']}**")
                st.markdown(f"SLA : **{result['sla_heures']}h**")
                st.markdown(f"Relance : **{result['relance_programmee'][:16] if result['relance_programmee'] else '—'}**")

            with col_b:
                st.markdown("**Entités extraites**")
                entites = result["entites_extraites"]
                for k, v in entites.items():
                    if v:
                        st.markdown(f"{k} : **{v}**")

            st.divider()
            st.markdown("**Actions exécutées**")
            for action in result["actions_executees"]:
                st.markdown(f"✅ {action}")

        with tab2:
            if result["reponse_generee"]:
                st.text_area("Réponse", value=result["reponse_generee"], height=300)
                if mode_demo:
                    st.info("Mode démo — réponse non envoyée.")
                else:
                    st.success(f"Email envoyé à {expediteur}")
            else:
                st.info("Aucune réponse générée — email classé comme spam ou non pertinent.")

        with tab3:
            for entry in result["audit_log"]:
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

            st.divider()
            st.download_button(
                label="📦 Télécharger Audit Trail JSON",
                data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
                file_name=f"audit_{result['ticket_reference']}.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab4:
            st.markdown("**Contact CRM**")
            if result["contact_data"]:
                st.json(result["contact_data"])
            else:
                st.info("Contact non trouvé dans le CRM.")

            st.markdown("**Historique interactions**")
            if result["historique_interactions"]:
                import pandas as pd
                st.dataframe(pd.DataFrame(result["historique_interactions"]), use_container_width=True, hide_index=True)
            else:
                st.info("Aucun historique disponible.")