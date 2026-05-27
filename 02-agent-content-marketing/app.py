# app.py
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import TONS, SECTEURS


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
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    sections = [
        ("ARTICLE DE BLOG", result["article_blog"]),
        ("POST LINKEDIN", result["post_linkedin"]),
        ("THREAD TWITTER/X", result["post_twitter"]),
    ]

    for titre, contenu in sections:
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=14)
        pdf.multi_cell(largeur, 10, nettoyer(titre))
        pdf.set_font("Helvetica", size=10)
        pdf.ln(4)
        for ligne in contenu.split("\n"):
            ligne = nettoyer(ligne.strip())
            if not ligne:
                pdf.ln(3)
                continue
            if ligne.startswith("#"):
                pdf.set_font("Helvetica", style="B", size=11)
                pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
                pdf.set_font("Helvetica", size=10)
            else:
                pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent Content Marketing AI", page_icon="✍️", layout="wide")
st.title("✍️ Agent Content Marketing Multicanal AI")
st.caption("Brief → Recherche web → Article blog + Post LinkedIn + Thread Twitter/X")

with st.form("form_content"):
    st.subheader("Brief")
    col1, col2, col3 = st.columns(3)
    secteur = col1.selectbox("Secteur", SECTEURS)
    ton = col2.selectbox("Ton", TONS)
    cible = col3.text_input("Cible", placeholder="Dirigeants PME, Dev senior, RH...")

    sujet = st.text_area(
        "Sujet / Brief",
        placeholder="L'impact de l'IA generative sur la productivite des equipes marketing en 2025",
        height=100,
    )

    submit = st.form_submit_button("Generer le contenu", use_container_width=True)

if submit:
    if not sujet or not cible:
        st.error("Merci de remplir le sujet et la cible.")
    else:
        with st.spinner("Recherche + generation en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "sujet": sujet,
                    "secteur": secteur,
                    "ton": ton,
                    "cible": cible,
                    "contexte_recherche": "",
                    "article_blog": "",
                    "post_linkedin": "",
                    "post_twitter": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        st.success("Contenu genere avec succes !")

        tab1, tab2, tab3 = st.tabs(["Article de blog", "Post LinkedIn", "Thread Twitter/X"])

        with tab1:
            st.markdown(result["article_blog"])

        with tab2:
            st.text_area("Post LinkedIn", value=result["post_linkedin"], height=400)
            if st.button("Copier LinkedIn"):
                st.write(result["post_linkedin"])

        with tab3:
            st.text_area("Thread Twitter/X", value=result["post_twitter"], height=400)

        try:
            pdf_bytes = generer_pdf(result)
            st.download_button(
                label="Telecharger tout en PDF",
                data=pdf_bytes,
                file_name=f"content_{sujet[:30].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as e:
            st.warning(f"Export PDF indisponible : {e}")