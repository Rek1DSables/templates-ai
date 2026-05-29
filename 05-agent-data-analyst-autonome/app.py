# app.py
import streamlit as st
from graph import build_graph
from config import CATEGORIES, PRIORITES


st.set_page_config(page_title="Agent Email Entrant", page_icon="📧", layout="centered")
st.title("📧 Agent Email Entrant")
st.caption("Collecte, classification, réponse automatique et routage des emails entrants")

col1, col2 = st.columns(2)
with col1:
    mode_demo = st.toggle("Mode démo (sans Gmail réel)", value=True)
with col2:
    repondre_auto = st.toggle("Répondre automatiquement", value=False)

if not mode_demo:
    st.info("Mode Gmail réel — les emails non lus de ta boîte seront traités.")
    st.warning("Assure-toi que credentials.json et token.json sont présents.")

if repondre_auto and not mode_demo:
    st.warning("⚠️ Les réponses seront envoyées automatiquement depuis ta boîte Gmail.")

if st.button("Traiter les emails entrants", use_container_width=True):
    with st.spinner("Collecte et analyse des emails en cours..."):
        try:
            graph = build_graph()
            result = graph.invoke({
                "emails_bruts": [],
                "emails_traites": [],
                "mode_demo": mode_demo,
                "repondre_auto": repondre_auto,
                "erreur": "",
            })
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.stop()

    if result["erreur"]:
        st.warning(result["erreur"])

    emails = result["emails_traites"]

    if not emails:
        st.info("Aucun email à traiter.")
    else:
        # Stats
        nb_urgent = sum(1 for e in emails if e.get("priorite") == "urgente")
        nb_spam = sum(1 for e in emails if e.get("categorie") == "Spam")
        nb_traites = len(emails) - nb_spam

        col1, col2, col3 = st.columns(3)
        col1.metric("Emails traités", nb_traites)
        col2.metric("Urgents", nb_urgent)
        col3.metric("Spam détecté", nb_spam)

        st.divider()

        # Tri par priorité
        ordre_priorite = {"urgente": 0, "haute": 1, "normale": 2, "basse": 3}
        emails_tries = sorted(emails, key=lambda x: ordre_priorite.get(x.get("priorite", "normale"), 2))

        for email in emails_tries:
            priorite = email.get("priorite", "normale")
            icone_priorite = PRIORITES.get(priorite, "🟡")
            categorie = email.get("categorie", "Autre")
            sentiment = email.get("sentiment", "neutre")
            icone_sentiment = "😊" if sentiment == "positif" else "😠" if sentiment == "negatif" else "😐"

            with st.expander(f"{icone_priorite} {email.get('sujet', 'Sans objet')} — {categorie}"):
                col_a, col_b, col_c = st.columns(3)
                col_a.markdown(f"**De :** {email.get('expediteur', '')}")
                col_b.markdown(f"**Priorité :** {icone_priorite} {priorite.capitalize()}")
                col_c.markdown(f"**Sentiment :** {icone_sentiment} {sentiment.capitalize()}")

                st.markdown(f"**Résumé :** {email.get('resume', '')}")
                st.markdown(f"**Action recommandée :** {email.get('action_recommandee', '')}")

                if email.get("reponse_suggeree"):
                    st.divider()
                    st.markdown("**Réponse suggérée :**")
                    st.text_area(
                        label="",
                        value=email.get("reponse_suggeree", ""),
                        height=150,
                        key=f"reponse_{email.get('id', '')}",
                    )

        if repondre_auto and not mode_demo:
            st.success("Réponses envoyées automatiquement.")
        elif mode_demo:
            st.info("Mode démo — aucune réponse envoyée. Active le mode Gmail réel pour envoyer.")