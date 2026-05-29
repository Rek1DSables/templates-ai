# app.py
import json
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import TYPES_DD, AXES_ANALYSE, NIVEAUX_RISQUE


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


def generer_pdf(result: dict, nom_cible: str, type_dd: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"RAPPORT DE DUE DILIGENCE — {nom_cible.upper()}"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Type : {type_dd}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Score global : {result['score_global']}/100"))
    pdf.ln(4)

    for ligne in result["synthese"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or ligne.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=12)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent Due Diligence", page_icon="🔍", layout="centered")
st.title("🔍 Agent Due Diligence")
st.caption("Analyse multi-axes + Matrice des risques + Rapport professionnel PDF")

st.subheader("Paramètres de l'opération")

col1, col2 = st.columns(2)
with col1:
    type_dd = st.selectbox("Type de due diligence", TYPES_DD)
    nom_cible = st.text_input("Nom de la cible", placeholder="Startup XYZ SAS")
with col2:
    secteur = st.text_input("Secteur", placeholder="SaaS B2B / Fintech / Industrie...")
    contexte = st.text_area("Contexte de l'opération", placeholder="Ex : Acquisition envisagée pour 2M€, cible en croissance de 40%, cherchons à valider la solidité financière et juridique.", height=80)

st.divider()
st.subheader("Axes d'analyse")
axes_selectionnes = st.multiselect(
    "Sélectionne les axes à analyser",
    AXES_ANALYSE,
    default=["Financier", "Juridique et contractuel", "Commercial et marché"],
)

st.divider()
st.subheader("Documents et informations par axe")
st.caption("Colle les informations disponibles pour chaque axe sélectionné")

documents = {}
for axe in axes_selectionnes:
    documents[axe] = st.text_area(
        f"📁 {axe}",
        placeholder=f"Colle ici les informations disponibles pour l'axe {axe} : bilans, contrats, KPIs, organigramme...",
        height=120,
        key=f"doc_{axe}",
    )

if st.button("Lancer la due diligence", use_container_width=True):
    if not nom_cible or not axes_selectionnes:
        st.error("Merci de renseigner le nom de la cible et au moins un axe d'analyse.")
    else:
        with st.spinner("Analyse en cours — cela peut prendre 1-2 minutes..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_dd": type_dd,
                    "nom_cible": nom_cible,
                    "secteur": secteur,
                    "contexte": contexte,
                    "documents": documents,
                    "axes_selectionnes": axes_selectionnes,
                    "analyse_par_axe": {},
                    "risques": [],
                    "score_global": 0,
                    "synthese": "",
                    "recommandation": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_global"]
        couleur = "🔴" if score < 40 else "🟠" if score < 60 else "🟡" if score < 75 else "🟢"

        col1, col2, col3 = st.columns(3)
        col1.metric("Cible", nom_cible)
        col2.metric("Score global", f"{couleur} {score}/100")
        col3.metric("Risques identifiés", len(result["risques"]))

        # Risques critiques
        risques_critiques = [r for r in result["risques"] if r.get("niveau") == "critique"]
        if risques_critiques:
            st.error(f"🔴 {len(risques_critiques)} risque(s) CRITIQUE(S) identifié(s)")

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Rapport complet",
            "Matrice des risques",
            "Scores par axe",
            "Export PDF",
        ])

        with tab1:
            st.markdown(result["synthese"])

        with tab2:
            risques = result["risques"]
            if not risques:
                st.success("Aucun risque majeur identifié.")
            else:
                for niveau in ["critique", "eleve", "moyen", "faible"]:
                    risques_niveau = [r for r in risques if r.get("niveau") == niveau]
                    if risques_niveau:
                        icone = NIVEAUX_RISQUE.get(niveau, "🟡")
                        st.subheader(f"{icone} Risques {niveau.capitalize()} ({len(risques_niveau)})")
                        for r in risques_niveau:
                            with st.expander(f"{r.get('titre', 'Risque')} — {r.get('axe', '')}"):
                                st.markdown(f"**Description :** {r.get('description', '')}")
                                st.markdown(f"**Impact :** {r.get('impact', '')}")
                                st.info(f"**Mitigation :** {r.get('mitigation', '')}")

        with tab3:
            import pandas as pd
            scores = []
            for axe, data in result["analyse_par_axe"].items():
                scores.append({
                    "Axe": axe,
                    "Note": f"{data.get('note', '?')}/10",
                    "Points positifs": len(data.get("points_positifs", [])),
                    "Points négatifs": len(data.get("points_negatifs", [])),
                    "Risques": len(data.get("risques", [])),
                })
            if scores:
                st.dataframe(pd.DataFrame(scores), use_container_width=True, hide_index=True)

        with tab4:
            try:
                pdf_bytes = generer_pdf(result, nom_cible, type_dd)
                st.download_button(
                    label="📄 Télécharger rapport PDF",
                    data=pdf_bytes,
                    file_name=f"due_diligence_{nom_cible.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")