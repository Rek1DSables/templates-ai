# app.py
import streamlit as st
from fpdf import FPDF
from graph import build_graph

EXEMPLES = [
    "Analyse le marche de l'IA generative en Europe en 2025 et redige un rapport executif",
    "Etudie les meilleures pratiques DevOps en 2025 et propose un plan d'implementation",
    "Analyse la concurrence entre LangChain et LlamaIndex et redige une recommandation technique",
    "Etudie les tendances du freelancing tech en France et propose une strategie de positionnement",
]


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


def generer_pdf(tache: str, synthese: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)

    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    # Titre
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer("Rapport - Orchestrateur Multi-Agents AI"))
    pdf.ln(2)

    # Tache
    pdf.set_font("Helvetica", style="B", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Tache : {tache}"))
    pdf.ln(4)

    # Contenu
    pdf.set_font("Helvetica", size=10)
    for ligne in synthese.split("\n"):
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
st.set_page_config(page_title="Orchestrateur Multi-Agents AI", page_icon="🧠", layout="wide")
st.title("🧠 Orchestrateur Multi-Agents AI")
st.caption("Un orchestrateur decompose votre tache et dispatche vers des agents specialises")

with st.sidebar:
    st.subheader("Exemples de taches")
    for exemple in EXEMPLES:
        if st.button(exemple[:60] + "...", use_container_width=True):
            st.session_state["tache"] = exemple

tache = st.text_area(
    "Tache complexe a traiter",
    value=st.session_state.get("tache", ""),
    placeholder="Analyse le marche de l'IA generative en Europe en 2025 et redige un rapport executif",
    height=120,
)

if st.button("Lancer l'orchestration", use_container_width=True):
    if not tache.strip():
        st.error("Merci de saisir une tache.")
    else:
        with st.spinner("Orchestration en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "tache": tache,
                    "sous_taches": [],
                    "resultats_agents": {},
                    "synthese": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success(f"Orchestration terminee — {len(result['sous_taches'])} agents utilises")

            tab1, tab2 = st.tabs(["Livrable finale", "Detail des agents"])

            with tab1:
                st.markdown(result["synthese"])

                try:
                    pdf_bytes = generer_pdf(tache, result["synthese"])
                    st.download_button(
                        label="Telecharger le rapport PDF",
                        data=pdf_bytes,
                        file_name="rapport_orchestrateur.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"Export PDF indisponible : {e}")

            with tab2:
                st.subheader("Decomposition de la tache")
                for sous_tache in result["sous_taches"]:
                    with st.expander(f"Agent {sous_tache['agent'].upper()} — Tache {sous_tache['id']}"):
                        st.caption(f"Instruction : {sous_tache['instruction']}")
                        id_tache = sous_tache["id"]
                        if id_tache in result["resultats_agents"]:
                            st.text_area(
                                "Resultat",
                                value=result["resultats_agents"][id_tache]["resultat"],
                                height=200,
                                key=f"agent_{id_tache}",
                            )