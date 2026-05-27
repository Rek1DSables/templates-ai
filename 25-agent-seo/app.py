# app.py
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import TYPES_SITE, SECTEURS


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


def generer_pdf(result: dict, url: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer("RAPPORT D'AUDIT SEO"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 7, nettoyer(f"URL : {url}"))
    pdf.multi_cell(largeur, 7, nettoyer(f"Score SEO : {result['score_seo']}/100"))
    pdf.ln(4)

    sections = [
        ("ANALYSE TECHNIQUE", result["analyse_technique"]),
        ("ANALYSE MOTS-CLES", result["analyse_mots_cles"]),
        ("ANALYSE CONCURRENCE", result["analyse_concurrence"]),
        ("RAPPORT ET PLAN D'ACTION", result["rapport_seo"]),
    ]

    for titre, contenu in sections:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 9, nettoyer(titre))
        pdf.set_font("Helvetica", size=10)
        pdf.ln(2)
        for ligne in contenu.split("\n"):
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
        pdf.ln(4)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent SEO AI", page_icon="🔍", layout="wide")
st.title("🔍 Agent SEO AI")
st.caption("Audit technique + Analyse mots-cles + Concurrence + Rapport PDF")

with st.form("form_seo"):
    st.subheader("Site a analyser")
    url = st.text_input("URL", placeholder="https://monsite.fr")

    col1, col2 = st.columns(2)
    type_site = col1.selectbox("Type de site", TYPES_SITE)
    secteur = col2.selectbox("Secteur", SECTEURS)

    mots_cles_input = st.text_input(
        "Mots-cles cibles (separes par des virgules)",
        placeholder="agent IA freelance, automatisation Python, LangGraph tutoriel"
    )

    submit = st.form_submit_button("Lancer l'audit SEO", use_container_width=True)

if submit:
    if not url or not mots_cles_input:
        st.error("Merci de remplir l'URL et les mots-cles.")
    else:
        if not url.startswith("http"):
            url = "https://" + url

        mots_cles = [mc.strip() for mc in mots_cles_input.split(",") if mc.strip()]

        with st.spinner("Audit SEO en cours : scraping, analyse mots-cles, concurrence..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "url": url,
                    "mots_cles": mots_cles,
                    "type_site": type_site,
                    "secteur": secteur,
                    "contenu_page": "",
                    "analyse_technique": "",
                    "analyse_mots_cles": "",
                    "analyse_concurrence": "",
                    "rapport_seo": "",
                    "score_seo": 0,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        score = result["score_seo"]
        couleur = "green" if score >= 70 else "orange" if score >= 40 else "red"

        col1, col2, col3 = st.columns(3)
        col1.metric("URL analysee", url[:40] + "..." if len(url) > 40 else url)
        col2.metric("Mots-cles analyses", len(mots_cles))
        col3.metric("Score SEO", f"{score}/100")

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Rapport & Plan d'action",
            "Analyse technique",
            "Mots-cles",
            "Concurrence",
        ])

        with tab1:
            st.markdown(result["rapport_seo"])
            try:
                pdf_bytes = generer_pdf(result, url)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"audit_seo_{url.replace('https://', '').replace('/', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")

        with tab2:
            st.markdown(result["analyse_technique"])

        with tab3:
            st.markdown(result["analyse_mots_cles"])

        with tab4:
            st.markdown(result["analyse_concurrence"])