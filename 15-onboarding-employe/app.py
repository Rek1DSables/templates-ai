# app.py
import os
import base64
import streamlit as st
from datetime import date
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from email.mime.text import MIMEText
from supabase import create_client
from graph import build_graph
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE,
    GMAIL_SENDER
)

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")


def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)


def envoyer_email(destinataire: str, contenu_email: str):
    try:
        lignes = contenu_email.strip().split("\n")
        objet = "Bienvenue dans l'equipe"
        corps_lignes = []
        for ligne in lignes:
            if ligne.startswith("Objet:"):
                objet = ligne.replace("Objet:", "").strip()
            else:
                corps_lignes.append(ligne)
        corps = "\n".join(corps_lignes).strip()

        service = get_gmail_service()
        message = MIMEText(corps)
        message["to"] = destinataire
        message["from"] = GMAIL_SENDER
        message["subject"] = objet
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        return True, ""
    except Exception as e:
        return False, str(e)


def sauvegarder_supabase(data: dict):
    if not supabase:
        return
    try:
        supabase.table(SUPABASE_TABLE).insert(data).execute()
    except Exception as e:
        st.warning(f"Erreur Supabase : {e}")


# --- UI ---
st.set_page_config(page_title="Onboarding Employe AI", page_icon="🧑‍💼", layout="centered")
st.title("🧑‍💼 Pipeline Onboarding Employe AI")
st.caption("Generation automatique du kit d'accueil pour les nouveaux employes")

with st.form("form_onboarding"):
    st.subheader("Informations employe")
    col1, col2 = st.columns(2)
    prenom = col1.text_input("Prenom", placeholder="Marie")
    nom = col2.text_input("Nom", placeholder="Dupont")

    col3, col4 = st.columns(2)
    poste = col3.text_input("Poste", placeholder="Developpeur Backend")
    departement = col4.text_input("Departement", placeholder="Tech")

    col5, col6 = st.columns(2)
    manager = col5.text_input("Manager", placeholder="Jean Martin")
    date_arrivee = col6.date_input("Date d'arrivee", value=date.today())

    email_employe = st.text_input("Email employe", placeholder="marie.dupont@entreprise.com")

    envoyer_gmail = st.checkbox("Envoyer l'email de bienvenue via Gmail", value=False)

    submit = st.form_submit_button("Generer le kit d'onboarding", use_container_width=True)

if submit:
    champs = [prenom, nom, poste, departement, manager, email_employe]
    if not all(champs):
        st.error("Merci de remplir tous les champs.")
    else:
        with st.spinner("Generation du kit d'onboarding en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "prenom": prenom,
                    "nom": nom,
                    "poste": poste,
                    "departement": departement,
                    "date_arrivee": str(date_arrivee),
                    "manager": manager,
                    "email_employe": email_employe,
                    "email_bienvenue": "",
                    "checklist": "",
                    "acces": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success("Kit d'onboarding genere avec succes !")

            tab1, tab2, tab3 = st.tabs(["Email de bienvenue", "Checklist onboarding", "Acces a provisionner"])

            with tab1:
                st.text_area("Email", value=result["email_bienvenue"], height=300)

            with tab2:
                st.text_area("Checklist", value=result["checklist"], height=300)

            with tab3:
                st.text_area("Acces", value=result["acces"], height=300)

            if envoyer_gmail and email_employe:
                with st.spinner("Envoi de l'email via Gmail..."):
                    succes, erreur_mail = envoyer_email(email_employe, result["email_bienvenue"])
                if succes:
                    st.success(f"Email envoye a {email_employe}")
                else:
                    st.error(f"Erreur envoi Gmail : {erreur_mail}")

            sauvegarder_supabase({
                "prenom": prenom,
                "nom": nom,
                "poste": poste,
                "departement": departement,
                "manager": manager,
                "date_arrivee": str(date_arrivee),
                "email_employe": email_employe,
                "email_bienvenue": result["email_bienvenue"],
                "checklist": result["checklist"],
                "acces": result["acces"],
            })