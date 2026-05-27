# app.py
import streamlit as st
from datetime import date
from supabase import create_client
from graph import build_graph
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")


def sauvegarder_supabase(data: dict):
    if not supabase:
        return
    try:
        supabase.table(SUPABASE_TABLE).insert(data).execute()
    except Exception as e:
        st.warning(f"Erreur Supabase : {e}")


# --- UI ---
st.set_page_config(page_title="Transcription & Resume de Reunions AI", page_icon="🎙️", layout="centered")
st.title("🎙️ Transcription & Resume de Reunions AI")
st.caption("Nettoyage, resume executif et extraction des action items depuis un transcript de reunion")

with st.form("form_reunion"):
    st.subheader("Informations de la reunion")
    col1, col2 = st.columns(2)
    titre = col1.text_input("Titre de la reunion", placeholder="Revue de sprint Q2")
    date_reunion = col2.date_input("Date", value=date.today())

    participants = st.text_input(
        "Participants",
        placeholder="Alice (PO), Bob (Dev), Claire (Design)"
    )

    st.subheader("Transcript")
    source = st.radio("Source du transcript", ["Coller le texte", "Uploader un fichier .txt"], horizontal=True)

    transcript_brut = ""
    if source == "Coller le texte":
        transcript_brut = st.text_area(
            "Transcript brut",
            placeholder="Alice : Bonjour tout le monde on commence...\nBob : Oui donc euh le sprint s'est bien passe...",
            height=200,
        )
    else:
        fichier = st.file_uploader("Fichier .txt", type=["txt"])
        if fichier:
            transcript_brut = fichier.read().decode("utf-8")
            st.text_area("Apercu", value=transcript_brut[:500] + "...", height=100, disabled=True)

    submit = st.form_submit_button("Analyser la reunion", use_container_width=True)

if submit:
    if not titre or not participants or not transcript_brut:
        st.error("Merci de remplir tous les champs et de fournir un transcript.")
    else:
        with st.spinner("Analyse en cours : nettoyage, resume, action items..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "titre": titre,
                    "date_reunion": str(date_reunion),
                    "participants": participants,
                    "transcript_brut": transcript_brut,
                    "transcript_nettoye": "",
                    "resume": "",
                    "action_items": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success("Analyse terminee !")

            tab1, tab2, tab3 = st.tabs(["Resume executif", "Action items", "Transcript nettoye"])

            with tab1:
                st.text_area("Resume", value=result["resume"], height=350)

            with tab2:
                st.text_area("Action items", value=result["action_items"], height=350)

            with tab3:
                st.text_area("Transcript nettoye", value=result["transcript_nettoye"], height=350)

            sauvegarder_supabase({
                "titre": titre,
                "date_reunion": str(date_reunion),
                "participants": participants,
                "transcript_brut": transcript_brut,
                "transcript_nettoye": result["transcript_nettoye"],
                "resume": result["resume"],
                "action_items": result["action_items"],
            })