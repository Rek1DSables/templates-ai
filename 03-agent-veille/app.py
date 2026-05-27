# app.py
import streamlit as st
from datetime import date
from fpdf import FPDF
from supabase import create_client
from graph import build_graph
from config import (
    SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE,
    TYPES_VEILLE
)

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")

ALERTE_CONFIG = {
    "critique": ("🔴 CRITIQUE", "error"),
    "important": ("🟠 IMPORTANT", "warning"),
    "informatif": ("🟢 INFORMATIF", "success"),
}


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


def generer_pdf(result: dict, entreprise: str, secteur: str, type_veille: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer("RAPPORT DE VEILLE STRATEGIQUE"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Entreprise : {entreprise} | Secteur : {secteur} | Type : {type_veille}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Niveau d'alerte : {result['niveau_alerte'].upper()} | Date : {str(date.today())}"))
    pdf.ln(4)

    if result["points_cles"]:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 8, nettoyer("POINTS CLES"))
        pdf.set_font("Helvetica", size=10)
        for point in result["points_cles"]:
            pdf.multi_cell(largeur, 6, nettoyer(f"- {point}"))
        pdf.ln(4)

    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("RAPPORT COMPLET"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["analyse"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or ligne.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
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
st.set_page_config(page_title="Agent Veille Multi-Sources AI", page_icon="🔍", layout="wide")
st.title("🔍 Agent de Veille Multi-Sources AI")
st.caption("Veille concurrentielle, sectorielle, reglementaire et technologique en un pipeline")

with st.sidebar:
    st.subheader("Historique des veilles")
    if supabase:
        try:
            historique = supabase.table(SUPABASE_TABLE).select("*").order("created_at", desc=True).limit(10).execute()
            for item in historique.data:
                alerte = item.get("niveau_alerte", "informatif")
                emoji = "🔴" if alerte == "critique" else "🟠" if alerte == "important" else "🟢"
                st.caption(f"{emoji} {item.get('type_veille')} — {item.get('entreprise')} — {item.get('date_veille', '')}")
        except:
            st.caption("Aucun historique disponible.")
    else:
        st.caption("Supabase non connecte.")

with st.form("form_veille"):
    st.subheader("Configuration de la veille")
    col1, col2, col3 = st.columns(3)
    entreprise = col1.text_input("Entreprise", placeholder="Acme Corp")
    secteur = col2.text_input("Secteur", placeholder="SaaS B2B, Fintech, E-commerce...")
    type_veille = col3.selectbox("Type de veille", TYPES_VEILLE)

    st.subheader("Sujets a surveiller")
    col4, col5 = st.columns(2)
    sujet1 = col4.text_input("Sujet 1", placeholder="Nom concurrent principal")
    sujet2 = col5.text_input("Sujet 2", placeholder="Technologie emergente")
    col6, col7 = st.columns(2)
    sujet3 = col6.text_input("Sujet 3", placeholder="Reglementation cle")
    sujet4 = col7.text_input("Sujet 4 (optionnel)", placeholder="Tendance marche")

    submit = st.form_submit_button("Lancer la veille", use_container_width=True)

if submit:
    if not entreprise or not secteur or not sujet1:
        st.error("Merci de remplir l'entreprise, le secteur et au moins un sujet.")
    else:
        sujets = [s for s in [sujet1, sujet2, sujet3, sujet4] if s.strip()]

        with st.spinner(f"Veille en cours sur {len(sujets)} sujets..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "entreprise": entreprise,
                    "secteur": secteur,
                    "type_veille": type_veille,
                    "sujets": sujets,
                    "resultats_bruts": {},
                    "analyse": "",
                    "niveau_alerte": "informatif",
                    "points_cles": [],
                    "recommandations": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        alerte = result["niveau_alerte"]
        label, niveau = ALERTE_CONFIG.get(alerte, ("🟢 INFORMATIF", "success"))
        getattr(st, niveau)(f"Niveau d'alerte : {label}")

        col1, col2, col3 = st.columns(3)
        col1.metric("Entreprise", entreprise)
        col2.metric("Type de veille", type_veille)
        col3.metric("Sujets surveilles", len(sujets))

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Rapport", "Points cles", "Sources brutes"])

        with tab1:
            st.markdown(result["analyse"])
            try:
                pdf_bytes = generer_pdf(result, entreprise, secteur, type_veille)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"veille_{entreprise.replace(' ', '_')}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")

        with tab2:
            for point in result["points_cles"]:
                st.markdown(f"- {point}")

        with tab3:
            for sujet, resultats in result["resultats_bruts"].items():
                with st.expander(f"Sources : {sujet}"):
                    st.text(resultats)

        sauvegarder_supabase({
            "entreprise": entreprise,
            "secteur": secteur,
            "type_veille": type_veille,
            "sujets": ", ".join(sujets),
            "niveau_alerte": alerte,
            "points_cles": "\n".join(result["points_cles"]),
            "rapport": result["analyse"],
            "date_veille": str(date.today()),
        })