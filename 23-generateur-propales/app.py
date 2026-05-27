# app.py
import streamlit as st
from datetime import date
from fpdf import FPDF
from supabase import create_client
from graph import build_graph
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE,
    TYPES_MISSION, MODES_FACTURATION
)

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")


def nettoyer(texte: str) -> str:
    remplacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00ab": '"', "\u00bb": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ",
    }
    for src, dst in remplacements.items():
        texte = texte.replace(src, dst)
    resultat = ""
    for char in texte:
        try:
            char.encode("latin-1")
            resultat += char
        except UnicodeEncodeError:
            resultat += " "
    return resultat


def generer_pdf(result: dict) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    # En-tete
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.multi_cell(largeur, 12, nettoyer("PROPOSITION COMMERCIALE"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Prestataire : {result['prestataire_nom']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Client : {result['client_nom']} — {result['client_entreprise']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Mission : {result['type_mission']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Budget : {result['budget']} | Delai : {result['delai']} | Date : {str(date.today())}"))
    pdf.ln(6)

    # Propale
    pdf.set_font("Helvetica", size=10)
    for ligne in result["propale_complete"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or (ligne.startswith("#")):
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        elif any(ligne.startswith(f"{i}.") for i in range(1, 10)):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 8, ligne)
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


def sauvegarder_supabase(data: dict):
    if not supabase:
        return
    try:
        supabase.table(SUPABASE_TABLE).insert(data).execute()
    except Exception as e:
        st.warning(f"Erreur Supabase : {e}")


# --- UI ---
st.set_page_config(page_title="Generateur de Propales AI", page_icon="📋", layout="wide")
st.title("📋 Generateur de Propositions Commerciales AI")
st.caption("Brief client → Analyse besoin → Solution → Propale complete + PDF")

with st.form("form_propale"):
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("Prestataire")
        prestataire_nom = st.text_input("Nom complet", placeholder="Jean Martin")
        prestataire_email = st.text_input("Email", placeholder="jean@freelance.fr")
        prestataire_expertise = st.text_area(
            "Expertise",
            placeholder="Expert AI Automation — LangGraph, Claude API, Supabase. 5 ans d'experience en automatisation de processus metier.",
            height=100,
        )

    with col_right:
        st.subheader("Client")
        client_nom = st.text_input("Nom contact", placeholder="Marie Dupont")
        client_entreprise = st.text_input("Entreprise", placeholder="Acme Corp")
        client_secteur = st.text_input("Secteur", placeholder="E-commerce, SaaS, Finance...")
        client_email = st.text_input("Email client", placeholder="marie@acme.com")

    st.subheader("Mission")
    col1, col2 = st.columns(2)
    type_mission = col1.selectbox("Type de mission", TYPES_MISSION)
    mode_facturation = col2.selectbox("Mode de facturation", MODES_FACTURATION)

    col3, col4 = st.columns(2)
    budget = col3.text_input("Budget", placeholder="8 000 EUR HT")
    delai = col4.text_input("Delai", placeholder="6 semaines")

    description_besoin = st.text_area(
        "Description du besoin",
        placeholder="Le client souhaite automatiser son processus de qualification de leads entrants. Actuellement traite manuellement par 2 commerciaux, 50 leads/semaine...",
        height=120,
    )

    objectifs = st.text_area(
        "Objectifs mesurables",
        placeholder="Reduire le temps de qualification de 4h a 30min/semaine. Augmenter le taux de conversion de 15% a 25%...",
        height=80,
    )

    submit = st.form_submit_button("Generer la proposition", use_container_width=True)

if submit:
    champs = [prestataire_nom, prestataire_email, client_nom, client_entreprise, description_besoin]
    if not all(champs):
        st.error("Merci de remplir tous les champs obligatoires.")
    else:
        with st.spinner("Generation de la proposition en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "prestataire_nom": prestataire_nom,
                    "prestataire_email": prestataire_email,
                    "prestataire_expertise": prestataire_expertise,
                    "client_nom": client_nom,
                    "client_entreprise": client_entreprise,
                    "client_secteur": client_secteur,
                    "client_email": client_email,
                    "type_mission": type_mission,
                    "description_besoin": description_besoin,
                    "objectifs": objectifs,
                    "budget": budget,
                    "delai": delai,
                    "mode_facturation": mode_facturation,
                    "analyse_besoin": "",
                    "solution_proposee": "",
                    "propale_complete": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        st.success("Proposition generee avec succes !")

        col1, col2, col3 = st.columns(3)
        col1.metric("Client", client_entreprise)
        col2.metric("Budget", budget)
        col3.metric("Delai", delai)

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Proposition complete", "Analyse & Solution", "Export PDF"])

        with tab1:
            st.markdown(result["propale_complete"])

        with tab2:
            st.subheader("Analyse du besoin")
            st.markdown(result["analyse_besoin"])
            st.subheader("Solution proposee")
            st.markdown(result["solution_proposee"])

        with tab3:
            try:
                pdf_bytes = generer_pdf(result)
                st.download_button(
                    label="Telecharger la proposition PDF",
                    data=pdf_bytes,
                    file_name=f"propale_{client_entreprise.replace(' ', '_')}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")

        sauvegarder_supabase({
            "prestataire_nom": prestataire_nom,
            "client_nom": client_nom,
            "client_entreprise": client_entreprise,
            "type_mission": type_mission,
            "budget": budget,
            "delai": delai,
            "mode_facturation": mode_facturation,
            "propale": result["propale_complete"],
            "date_propale": str(date.today()),
        })