# app.py
import streamlit as st
import pymupdf
from fpdf import FPDF
from graph import build_graph
from config import TYPES_CONTRAT, NIVEAUX_RISQUE


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


def extraire_texte_pdf(fichier) -> str:
    try:
        pdf_bytes = fichier.read()
        doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
        texte = ""
        for page in doc:
            texte += page.get_text()
        return texte.strip()
    except Exception as e:
        return f"Erreur extraction PDF : {str(e)}"


def generer_pdf_rapport(result: dict, type_contrat: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer("RAPPORT D'ANALYSE CONTRACTUELLE"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Type : {type_contrat}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Score de risque : {result['score_risque']}/100"))
    pdf.ln(4)

    sections = [
        ("RESUME EXECUTIF ET RECOMMANDATIONS", result["resume_executif"]),
        ("RISQUES IDENTIFIES", result["risques"]),
        ("CLAUSES EXTRAITES", result["clauses_extraites"]),
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
st.set_page_config(page_title="Analyseur de Contrats AI", page_icon="📜", layout="centered")
st.title("📜 Analyseur de Contrats AI")
st.caption("Upload PDF ou texte → Extraction clauses → Analyse risques → Recommandations + PDF")

type_contrat = st.selectbox("Type de contrat", TYPES_CONTRAT)

st.subheader("Source du contrat")
source = st.radio("Source", ["Uploader un PDF", "Coller le texte"], horizontal=True)

fichier = None
texte_direct = ""

if source == "Uploader un PDF":
    fichier = st.file_uploader("Fichier PDF", type=["pdf"])
else:
    texte_direct = st.text_area(
        "Texte du contrat",
        placeholder="Colle ici le contenu du contrat...",
        height=250,
    )

submit = st.button("Analyser le contrat", use_container_width=True)

if submit:
    contenu = ""
    if fichier:
        with st.spinner("Extraction du texte PDF..."):
            fichier.seek(0)
            contenu = extraire_texte_pdf(fichier)
    elif texte_direct:
        contenu = texte_direct

    if not contenu:
        st.error("Merci d'uploader un PDF ou de coller le texte du contrat.")
    else:
        with st.spinner("Analyse en cours : extraction clauses, risques, recommandations..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_contrat": type_contrat,
                    "contenu_texte": contenu,
                    "clauses_extraites": "",
                    "risques": "",
                    "resume_executif": "",
                    "recommandations": "",
                    "score_risque": 0,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        score = result["score_risque"]
        couleur_score = "🔴" if score >= 70 else "🟠" if score >= 40 else "🟢"

        col1, col2 = st.columns(2)
        col1.metric("Type de contrat", type_contrat)
        col2.metric("Score de risque", f"{couleur_score} {score}/100")

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Resume & Recommandations",
            "Risques identifies",
            "Clauses extraites",
            "Export PDF",
        ])

        with tab1:
            st.markdown(result["resume_executif"])

        with tab2:
            st.markdown(result["risques"])

        with tab3:
            st.markdown(result["clauses_extraites"])

        with tab4:
            try:
                pdf_bytes = generer_pdf_rapport(result, type_contrat)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"analyse_contrat_{type_contrat.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")