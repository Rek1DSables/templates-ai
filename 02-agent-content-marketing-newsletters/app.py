# app.py
import streamlit as st
from graph import build_graph
from config import CANAUX_CONTENU, TONS, LONGUEURS


st.set_page_config(page_title="Agent Content Marketing & Newsletters", page_icon="✍️", layout="centered")
st.title("✍️ Agent Content Marketing & Newsletters")
st.caption("Génération de contenu multicanal + envoi newsletter par email")

with st.form("form_content"):
    st.subheader("Paramètres du contenu")

    col1, col2 = st.columns(2)
    with col1:
        canal = st.selectbox("Canal", CANAUX_CONTENU)
        ton = st.selectbox("Ton", TONS)
    with col2:
        longueur = st.selectbox("Longueur", list(LONGUEURS.keys()))
        audience = st.text_input("Audience cible", placeholder="Entrepreneurs, développeurs, PME...")

    sujet = st.text_input("Sujet / Thème", placeholder="L'IA générative dans les PME en 2025")
    contexte = st.text_area("Contexte supplémentaire (optionnel)", placeholder="Points clés à aborder, angle spécifique...", height=80)

    st.divider()
    st.subheader("Envoi email (optionnel)")
    envoyer_email = st.checkbox("Envoyer par email après génération")
    destinataire_email = ""
    objet_email = ""
    if envoyer_email:
        destinataire_email = st.text_input("Email destinataire", placeholder="contact@client.com")
        objet_email = st.text_input("Objet de l'email", placeholder="Newsletter : L'IA en 2025")

    submit = st.form_submit_button("Générer le contenu", use_container_width=True)

if submit:
    if not sujet:
        st.error("Merci de renseigner un sujet.")
    else:
        with st.spinner("Recherche de contexte et génération en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "sujet": sujet,
                    "canal": canal,
                    "ton": ton,
                    "longueur": longueur,
                    "audience": audience,
                    "contexte": contexte,
                    "envoyer_email": envoyer_email,
                    "destinataire_email": destinataire_email,
                    "objet_email": objet_email,
                    "resultats_recherche": "",
                    "contenu_genere": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        col1, col2 = st.columns(2)
        col1.metric("Canal", canal)
        col2.metric("Ton", ton)

        st.divider()

        tab1, tab2 = st.tabs(["Contenu généré", "Export"])

        with tab1:
            st.markdown(result["contenu_genere"])

        with tab2:
            st.download_button(
                label="📄 Télécharger TXT",
                data=result["contenu_genere"],
                file_name=f"contenu_{canal.lower().replace(' ', '_')}.txt",
                mime="text/plain",
                use_container_width=True,
            )

        if envoyer_email and destinataire_email and not result["erreur"]:
            st.success(f"Email envoyé à {destinataire_email}")