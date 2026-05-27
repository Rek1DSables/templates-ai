# app.py
import os
import base64
import streamlit as st
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
import uuid

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


def envoyer_email(destinataire: str, sujet: str, corps: str):
    try:
        service = get_gmail_service()
        message = MIMEText(corps)
        message["to"] = destinataire
        message["from"] = GMAIL_SENDER
        message["subject"] = f"Re: {sujet}"
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


DECISION_CONFIG = {
    "envoyer": ("✅ Reponse envoyee automatiquement", "success"),
    "escalader": ("🔴 Escalade vers un agent humain", "error"),
    "revoir": ("⚠️ Reponse a revoir manuellement", "warning"),
}

# --- UI ---
st.set_page_config(page_title="Support Client Enterprise AI", page_icon="🎧", layout="wide")
st.title("🎧 Support Client Enterprise Multi-Agents")
st.caption("Pipeline 4 agents : Classification → Knowledge Base → Redaction → Verification & Decision")

with st.sidebar:
    st.subheader("Pipeline")
    st.markdown("""
**Agent A** — Classification  
**Agent B** — Knowledge Base  
**Agent C** — Redaction  
**Agent D** — Verification & Decision
    """)
    st.divider()
    envoyer_gmail = st.checkbox("Envoyer via Gmail si decision = envoyer", value=False)

with st.form("form_ticket"):
    st.subheader("Ticket entrant")
    col1, col2 = st.columns(2)
    canal = col1.selectbox("Canal", ["Email", "Slack", "Webhook", "Chat"])
    expediteur = col2.text_input("Expediteur", placeholder="client@entreprise.com")

    sujet = st.text_input("Sujet", placeholder="Impossible de me connecter depuis ce matin")
    message = st.text_area("Message", placeholder="Bonjour, depuis ce matin je n'arrive plus a acceder a mon compte...", height=150)

    submit = st.form_submit_button("Traiter le ticket", use_container_width=True)

if submit:
    if not expediteur or not sujet or not message:
        st.error("Merci de remplir tous les champs.")
    else:
        ticket_id = str(uuid.uuid4())[:8].upper()

        with st.spinner("Pipeline 4 agents en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "ticket_id": ticket_id,
                    "canal": canal,
                    "expediteur": expediteur,
                    "sujet": sujet,
                    "message": message,
                    "categorie": "",
                    "priorite": "",
                    "score_complexite": 0,
                    "reponse_kb": "",
                    "reponse_redigee": "",
                    "score_confiance": 0,
                    "decision": "",
                    "justification": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ticket ID", f"#{result['ticket_id']}")
        col2.metric("Categorie", result["categorie"].upper())
        col3.metric("Priorite", result["priorite"].upper())
        col4.metric("Complexite", f"{result['score_complexite']}/10")

        st.divider()

        # Decision
        decision = result["decision"]
        label, niveau = DECISION_CONFIG.get(decision, ("Decision inconnue", "warning"))
        getattr(st, niveau)(f"{label} — Confiance : {result['score_confiance']}/10 — {result['justification']}")

        # Tabs
        tab1, tab2, tab3 = st.tabs(["Reponse redigee", "Knowledge Base", "Classification"])

        with tab1:
            st.text_area("Reponse", value=result["reponse_redigee"], height=300)
            if decision == "envoyer" and envoyer_gmail and expediteur:
                with st.spinner("Envoi Gmail..."):
                    succes, erreur_mail = envoyer_email(expediteur, sujet, result["reponse_redigee"])
                if succes:
                    st.success(f"Email envoye a {expediteur}")
                else:
                    st.error(f"Erreur Gmail : {erreur_mail}")

        with tab2:
            st.text_area("Solution KB", value=result["reponse_kb"], height=200)

        with tab3:
            st.json({
                "categorie": result["categorie"],
                "priorite": result["priorite"],
                "score_complexite": result["score_complexite"],
                "score_confiance": result["score_confiance"],
                "decision": result["decision"],
                "justification": result["justification"],
            })

        sauvegarder_supabase({
            "ticket_id": result["ticket_id"],
            "canal": canal,
            "expediteur": expediteur,
            "sujet": sujet,
            "message": message,
            "categorie": result["categorie"],
            "priorite": result["priorite"],
            "score_complexite": result["score_complexite"],
            "reponse_redigee": result["reponse_redigee"],
            "score_confiance": result["score_confiance"],
            "decision": result["decision"],
        })