# app.py
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import SECTEURS, TAILLES


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

    # Titre
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.multi_cell(largeur, 12, nettoyer("RAPPORT D'AUDIT IA"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Entreprise : {result['entreprise']} | Secteur : {result['secteur']}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Score global d'automatisabilite : {result['score_global']}/10"))
    pdf.ln(4)

    # Analyse
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.multi_cell(largeur, 10, nettoyer("ANALYSE DES PROCESSUS"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["analyse_processus"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        pdf.multi_cell(largeur, 6, ligne)
    pdf.ln(4)

    # Opportunites
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.multi_cell(largeur, 10, nettoyer("OPPORTUNITES D'AUTOMATISATION"))
    pdf.set_font("Helvetica", size=10)
    for i, opp in enumerate(result["opportunites"], 1):
        pdf.set_font("Helvetica", style="B", size=11)
        pdf.multi_cell(largeur, 8, nettoyer(f"{i}. {opp.get('tache', '')}"))
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(largeur, 6, nettoyer(f"Score : {opp.get('score_automatisabilite', '')}/10 | Gain : {opp.get('gain_temps_heures_semaine', '')}h/sem | ROI : {opp.get('roi_estime_mois', '')} mois | Priorite : {opp.get('priorite', '')}"))
        pdf.ln(2)
    pdf.ln(4)

    # Roadmap
    pdf.set_font("Helvetica", style="B", size=13)
    pdf.multi_cell(largeur, 10, nettoyer("ROADMAP D'IMPLEMENTATION"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["roadmap"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.startswith("#") or ligne.isupper():
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Audit IA Interne", page_icon="🔍", layout="wide")
st.title("🔍 Systeme d'Audit IA Interne")
st.caption("Analyse vos processus, identifie les opportunites d'automatisation et genere un roadmap priorise ROI")

with st.form("form_audit"):
    st.subheader("Informations entreprise")
    col1, col2, col3 = st.columns(3)
    entreprise = col1.text_input("Nom de l'entreprise", placeholder="Acme Corp")
    secteur = col2.selectbox("Secteur", SECTEURS)
    taille = col3.selectbox("Taille", TAILLES)

    budget_ia = st.selectbox(
        "Budget IA envisage",
        ["< 5 000 EUR", "5 000 - 20 000 EUR", "20 000 - 50 000 EUR", "50 000 - 100 000 EUR", "> 100 000 EUR"],
    )

    st.subheader("Description des processus")
    processus = st.text_area(
        "Decrivez vos processus metier actuels (le plus de detail possible)",
        placeholder="""Exemple :
- Traitement des commandes : reception par email, saisie manuelle dans Excel, envoi confirmation client
- Support client : 50 tickets/jour traites manuellement par 2 personnes, reponse sous 24h
- Facturation : creation manuelle des factures Word, envoi par email, relances manuelles
- Reporting : compilation hebdomadaire des KPIs depuis 5 sources differentes, 4h de travail
- Recrutement : tri manuel des CVs, emails de reponse individuels, planning entretiens manuel""",
        height=250,
    )

    submit = st.form_submit_button("Lancer l'audit IA", use_container_width=True)

if submit:
    if not entreprise or not processus:
        st.error("Merci de remplir le nom de l'entreprise et la description des processus.")
    else:
        with st.spinner("Audit en cours : analyse, opportunites, roadmap..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "entreprise": entreprise,
                    "secteur": secteur,
                    "taille": taille,
                    "budget_ia": budget_ia,
                    "processus": processus,
                    "analyse_processus": "",
                    "opportunites": [],
                    "roadmap": "",
                    "score_global": 0,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        # KPIs
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Entreprise", entreprise)
        col2.metric("Secteur", secteur)
        col3.metric("Opportunites", len(result["opportunites"]))
        col4.metric("Score automatisabilite", f"{result['score_global']}/10")

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Roadmap", "Opportunites", "Analyse processus"])

        with tab1:
            st.markdown(result["roadmap"])
            try:
                pdf_bytes = generer_pdf(result)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"audit_ia_{entreprise.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")

        with tab2:
            if result["opportunites"]:
                for i, opp in enumerate(result["opportunites"], 1):
                    with st.expander(f"{i}. {opp.get('tache', '')} — Score {opp.get('score_automatisabilite', '')}/10 — Priorite {opp.get('priorite', '').upper()}"):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Gain temps", f"{opp.get('gain_temps_heures_semaine', '')}h/sem")
                        col2.metric("ROI estime", f"{opp.get('roi_estime_mois', '')} mois")
                        col3.metric("Complexite", opp.get("complexite_implementation", ""))
                        st.caption(f"Technologie : {opp.get('technologie_recommandee', '')}")
                        st.caption(f"Delai implementation : {opp.get('delai_implementation_semaines', '')} semaines")
            else:
                st.info("Aucune opportunite identifiee.")

        with tab3:
            st.markdown(result["analyse_processus"])