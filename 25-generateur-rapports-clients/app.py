# app.py
import streamlit as st
from datetime import date
from fpdf import FPDF
from supabase import create_client
from graph import build_graph
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE,
    TYPES_MISSION, PERIODES
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

    pdf.set_font("Helvetica", style="B", size=16)
    pdf.multi_cell(largeur, 12, nettoyer("RAPPORT CLIENT"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Prestataire : {result['prestataire_nom']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Client : {result['client_nom']} - {result['client_entreprise']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Mission : {result['type_mission']} | Periode : {result['periode']} | Date : {result['date_rapport']}"))
    pdf.ln(6)

    pdf.set_font("Helvetica", size=10)
    for ligne in result["rapport_complet"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or ligne.startswith("#"):
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
st.set_page_config(page_title="Generateur Rapports Clients AI", page_icon="📊", layout="wide")
st.title("📊 Generateur de Rapports Clients AI")
st.caption("Saisie des realisations → Analyse performance → Rapport professionnel + PDF")

with st.form("form_rapport"):
    st.subheader("Informations de la mission")
    col1, col2 = st.columns(2)
    prestataire_nom = col1.text_input("Votre nom", placeholder="Jean Martin")
    client_entreprise = col2.text_input("Entreprise cliente", placeholder="Acme Corp")

    col3, col4 = st.columns(2)
    client_nom = col3.text_input("Contact client", placeholder="Marie Dupont")
    type_mission = col4.selectbox("Type de mission", TYPES_MISSION)

    col5, col6 = st.columns(2)
    periode = col5.selectbox("Periode", PERIODES)
    date_rapport = col6.date_input("Date du rapport", value=date.today())

    st.subheader("Realisations")
    taches_realisees = st.text_area(
        "Taches realisees cette periode",
        placeholder="- Developpement agent IA de qualification de leads\n- Integration Supabase\n- Deploiement Streamlit Cloud",
        height=150,
    )

    kpis = st.text_area(
        "KPIs et resultats obtenus",
        placeholder="- Agent operationnel : 95% de precision\n- Temps reduit de 4h a 20min/semaine\n- 47 leads traites automatiquement",
        height=120,
    )

    col7, col8 = st.columns(2)
    problemes_rencontres = col7.text_area(
        "Problemes rencontres (optionnel)",
        placeholder="- Limite tokens API → resolu avec chunking",
        height=100,
    )

    prochaines_etapes = col8.text_area(
        "Prochaines etapes (optionnel)",
        placeholder="- Integration Gmail\n- Dashboard analytics\n- Formation equipe",
        height=100,
    )

    submit = st.form_submit_button("Generer le rapport", use_container_width=True)

if submit:
    if not prestataire_nom or not client_nom or not client_entreprise or not taches_realisees or not kpis:
        st.error("Merci de remplir : votre nom, contact client, entreprise, taches et KPIs.")
    else:
        with st.spinner("Generation du rapport en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "prestataire_nom": prestataire_nom,
                    "client_nom": client_nom,
                    "client_entreprise": client_entreprise,
                    "type_mission": type_mission,
                    "periode": periode,
                    "date_rapport": str(date_rapport),
                    "taches_realisees": taches_realisees,
                    "kpis": kpis,
                    "problemes_rencontres": problemes_rencontres or "Aucun probleme majeur rencontre.",
                    "prochaines_etapes": prochaines_etapes or "A definir avec le client.",
                    "resume_executif": "",
                    "analyse_performance": "",
                    "rapport_complet": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        st.success("Rapport genere avec succes !")

        col1, col2, col3 = st.columns(3)
        col1.metric("Client", client_entreprise)
        col2.metric("Mission", type_mission)
        col3.metric("Periode", periode)

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Rapport complet", "Resume & Analyse", "Export PDF"])

        with tab1:
            st.markdown(result["rapport_complet"])

        with tab2:
            st.subheader("Resume executif")
            st.markdown(result["resume_executif"])
            st.subheader("Analyse de performance")
            st.markdown(result["analyse_performance"])

        with tab3:
            try:
                pdf_bytes = generer_pdf(result)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"rapport_{client_entreprise.replace(' ', '_')}_{date_rapport}.pdf",
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
            "periode": periode,
            "date_rapport": str(date_rapport),
            "rapport": result["rapport_complet"],
        })