# app.py
import os
import streamlit as st
from datetime import date
from fpdf import FPDF
from supabase import create_client
from graph import build_graph
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, PDF_OUTPUT_DIR

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")

os.makedirs(PDF_OUTPUT_DIR, exist_ok=True)


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


def generer_pdf(contenu: str, nom_fichier: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    pdf.set_font("Helvetica", size=11)

    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    for ligne in contenu.split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(4)
            continue
        if ligne.startswith("Article"):
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.multi_cell(largeur, 8, ligne)
            pdf.set_font("Helvetica", size=11)
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
st.set_page_config(page_title="Generateur de Contrats AI", page_icon="📄", layout="centered")
st.title("📄 Generateur de Contrats AI")
st.caption("Redaction automatique de contrats freelance professionnels")

with st.form("form_contrat"):
    st.subheader("Type de contrat")
    type_contrat = st.selectbox(
        "Type",
        ["Prestation de services", "Mission freelance", "Contrat de conseil", "Contrat de developpement"],
    )

    st.subheader("Prestataire (vous)")
    col1, col2 = st.columns(2)
    freelance_nom = col1.text_input("Nom complet", placeholder="Jean Dupont")
    freelance_email = col2.text_input("Email", placeholder="jean@email.com")

    st.subheader("Client")
    col3, col4 = st.columns(2)
    client_nom = col3.text_input("Nom / Societe", placeholder="Acme Corp")
    client_email = col4.text_input("Email client", placeholder="contact@acme.com")

    st.subheader("Mission")
    prestation = st.text_area(
        "Description de la prestation",
        placeholder="Developpement d une application web...",
        height=100,
    )
    col5, col6, col7 = st.columns(3)
    tarif = col5.text_input("Tarif", placeholder="500 EUR HT/jour")
    duree = col6.text_input("Duree", placeholder="3 mois")
    date_debut = col7.date_input("Date de debut", value=date.today())

    submit = st.form_submit_button("Generer le contrat", use_container_width=True)

if submit:
    champs = [freelance_nom, freelance_email, client_nom, client_email, prestation, tarif, duree]
    if not all(champs):
        st.error("Merci de remplir tous les champs.")
    else:
        with st.spinner("Redaction du contrat en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_contrat": type_contrat,
                    "freelance_nom": freelance_nom,
                    "freelance_email": freelance_email,
                    "client_nom": client_nom,
                    "client_email": client_email,
                    "prestation": prestation,
                    "tarif": tarif,
                    "duree": duree,
                    "date_debut": str(date_debut),
                    "contenu_genere": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success("Contrat genere avec succes !")

            with st.expander("Apercu du contrat", expanded=True):
                st.text(result["contenu_genere"])

            nom_fichier = f"contrat_{client_nom.replace(' ', '_')}_{date_debut}.pdf"

            try:
                pdf_bytes = generer_pdf(result["contenu_genere"], nom_fichier)
                st.download_button(
                    label="Telecharger le PDF",
                    data=pdf_bytes,
                    file_name=nom_fichier,
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erreur generation PDF : {e}")
                st.stop()

            sauvegarder_supabase({
                "type_contrat": type_contrat,
                "freelance_nom": freelance_nom,
                "client_nom": client_nom,
                "prestation": prestation,
                "tarif": tarif,
                "duree": duree,
                "date_debut": str(date_debut),
                "contenu": result["contenu_genere"],
            })