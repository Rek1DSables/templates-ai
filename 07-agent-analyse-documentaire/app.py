# app.py
import json
import time
import streamlit as st
import pandas as pd
from fpdf import FPDF
from graph import build_graph
from config import TYPES_DOCUMENTS, AXES_PAR_TYPE, AXES_DEFAUT, NIVEAUX_RISQUE

# Document de demo
CONTRAT_DEMO = """CONTRAT DE PRESTATION DE SERVICES INFORMATIQUES

Entre les soussignés :
La société TECHCORP SAS, société par actions simplifiée au capital de 50 000 euros, immatriculée au RCS de Paris sous le numéro 123 456 789, dont le siège social est situé au 42 avenue des Champs-Elysées, 75008 Paris, représentée par Monsieur Jean DUPONT en sa qualité de Directeur Général (ci-après "le Client")

ET

La société DEVAGENCY SARL, société à responsabilité limitée au capital de 10 000 euros, immatriculée au RCS de Lyon sous le numéro 987 654 321, dont le siège social est situé au 15 rue de la République, 69001 Lyon, représentée par Madame Marie MARTIN en sa qualité de Gérante (ci-après "le Prestataire")

ARTICLE 1 - OBJET
Le Prestataire s'engage à fournir des services de développement logiciel et de conseil en transformation numérique selon les spécifications définies en annexe.

ARTICLE 2 - DURÉE
Le présent contrat est conclu pour une durée de 12 mois à compter du 1er juin 2026, renouvelable par tacite reconduction pour des périodes successives de 12 mois sauf dénonciation par l'une des parties avec un préavis de 30 jours.

ARTICLE 3 - PRIX ET MODALITÉS DE PAIEMENT
Les prestations seront facturées au tarif journalier de 650 euros HT. Le paiement est exigible à 90 jours fin de mois, ce qui dépasse le délai légal maximum de 60 jours prévu par la loi LME.

ARTICLE 4 - RESPONSABILITÉ
Le Prestataire est responsable de tous les dommages directs et indirects causés dans le cadre de l'exécution du contrat, sans limitation de montant. Cette clause engage le Prestataire de manière illimitée et sans plafond.

ARTICLE 5 - PROPRIÉTÉ INTELLECTUELLE
Tous les développements réalisés dans le cadre de ce contrat deviennent la propriété exclusive du Client dès leur livraison, y compris les outils et méthodes génériques du Prestataire.

ARTICLE 6 - RÉSILIATION
Le Client peut résilier le contrat à tout moment sans préavis ni indemnité. Le Prestataire ne peut résilier qu'avec un préavis de 6 mois et uniquement en cas de faute grave du Client.

ARTICLE 7 - CONFIDENTIALITÉ
Les parties s'engagent à maintenir la confidentialité des informations échangées pendant la durée du contrat et pendant 5 ans après son terme.

ARTICLE 8 - LOI APPLICABLE
Le présent contrat est soumis au droit français. Tout litige sera soumis aux tribunaux de Paris."""


def nettoyer(texte: str) -> str:
    remplacements = {
        "\u2019": "'", "\u2018": "'", "\u201c": '"', "\u201d": '"',
        "\u00ab": '"', "\u00bb": '"', "\u2013": "-", "\u2014": "-",
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


def generer_pdf(result: dict, nom_document: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"ANALYSE DOCUMENTAIRE — {nom_document.upper()}"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Date : {time.strftime('%d/%m/%Y')} | Score risque : {result['score_risque']}/100"))
    pdf.ln(4)

    for ligne in result["synthese_complete"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(2)
            continue
        if ligne.isupper() or ligne.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 7, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    pdf.ln(4)
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("AUDIT TRAIL"))
    pdf.set_font("Helvetica", size=9)
    for entry in result["audit_log"]:
        pdf.multi_cell(largeur, 5, nettoyer(
            f"[{entry.get('timestamp')}] {entry.get('agent')} — {entry.get('etape')} {entry.get('detail', '')}"
        ))

    return bytes(pdf.output())


st.set_page_config(page_title="Agent Analyse Documentaire", page_icon="📑", layout="centered")
st.title("📑 Agent Analyse Documentaire Avancée")
st.caption("Pipeline multi-agents : Extraction structurée → Vérification risques → Synthèse → Recommandations")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Extraction** — extrait les données pour chaque axe d'analyse
2. **Agent Vérification Risques** — identifie les risques, vérifie la cohérence
3. **Agent Synthèse Partie 1** — executive summary + informations extraites
4. **Agent Synthèse Partie 2** — matrice risques + recommandations + verdict
    """)

st.divider()

type_document = st.selectbox("Type de document", TYPES_DOCUMENTS)
axes = AXES_PAR_TYPE.get(type_document, AXES_DEFAUT)

st.info(f"**{len(axes)} axes d'analyse** configurés pour ce type de document")

source = st.radio("Source du document", ["Document de démo (contrat commercial)", "Coller le texte", "Uploader un PDF"], horizontal=True)

contenu = ""
nom_document = ""

if source == "Document de démo (contrat commercial)":
    contenu = CONTRAT_DEMO
    nom_document = "Contrat Prestation TECHCORP-DEVAGENCY"
    type_document = "Contrat commercial"
    axes = AXES_PAR_TYPE.get(type_document, AXES_DEFAUT)
    with st.expander("Aperçu du document de démo"):
        st.text(CONTRAT_DEMO[:500] + "...")

elif source == "Coller le texte":
    nom_document = st.text_input("Nom du document", placeholder="Contrat XYZ")
    contenu = st.text_area("Contenu du document", height=250,
        placeholder="Colle ici le texte du document à analyser...")

else:
    nom_document = st.text_input("Nom du document", placeholder="Contrat XYZ")
    fichier = st.file_uploader("Fichier PDF", type=["pdf"])
    if fichier:
        try:
            import pymupdf
            pdf_bytes = fichier.read()
            doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
            contenu = ""
            for page in doc:
                contenu += page.get_text()
            st.success(f"PDF extrait : {len(contenu)} caractères")
        except Exception as e:
            st.error(f"Erreur extraction PDF : {e}")

if st.button("Analyser le document", use_container_width=True):
    if not contenu or not nom_document:
        st.error("Merci de fournir le document et son nom.")
    else:
        with st.spinner("Analyse multi-agents en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_document": type_document,
                    "contenu_document": contenu,
                    "nom_document": nom_document,
                    "axes_analyse": axes,
                    "extractions": {},
                    "risques": [],
                    "score_risque": 0,
                    "matrice_conformite": [],
                    "synthese_partie1": "",
                    "synthese_partie2": "",
                    "synthese_complete": "",
                    "recommandations": [],
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_risque"]
        couleur = "🔴" if score >= 70 else "🟠" if score >= 50 else "🟡" if score >= 30 else "🟢"
        nb_critiques = len([r for r in result["risques"] if r.get("niveau") == "critique"])

        col1, col2, col3 = st.columns(3)
        col1.metric("Score risque", f"{couleur} {score}/100")
        col2.metric("Risques identifiés", len(result["risques"]))
        col3.metric("Risques critiques", nb_critiques)

        if nb_critiques > 0:
            st.error(f"🚨 {nb_critiques} risque(s) CRITIQUE(S) — signature déconseillée sans négociation")

        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Synthèse & Recommandations",
            "Données extraites",
            "Matrice des risques",
            "Audit Trail",
            "Export PDF",
        ])

        with tab1:
            st.markdown(result["synthese_complete"])

        with tab2:
            rows = []
            for axe, data in result["extractions"].items():
                rows.append({
                    "Axe": axe,
                    "Présent": "✅" if data.get("present") else "❌",
                    "Valeur": str(data.get("valeur", "—") or "—")[:80],
                    "Fiabilité": data.get("fiabilite", "—"),
                    "Alerte": data.get("alerte", "") or "",
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        with tab3:
            risques = result["risques"]
            if not risques:
                st.success("Aucun risque majeur identifié.")
            else:
                for niveau in ["critique", "eleve", "moyen", "faible"]:
                    risques_niveau = [r for r in risques if r.get("niveau") == niveau]
                    if risques_niveau:
                        icone = NIVEAUX_RISQUE.get(niveau, "🟡")
                        st.subheader(f"{icone} {niveau.capitalize()} ({len(risques_niveau)})")
                        for r in risques_niveau:
                            with st.expander(f"{r.get('titre', 'Risque')}"):
                                st.markdown(f"**Axe :** {r.get('axe_concerne', '')}")
                                st.markdown(f"**Description :** {r.get('description', '')}")
                                st.markdown(f"**Impact :** {r.get('impact', '')}")
                                st.info(f"**Mitigation :** {r.get('mitigation', '')}")

        with tab4:
            for entry in result["audit_log"]:
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

            st.download_button(
                label="📦 Audit Trail JSON",
                data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
                file_name=f"audit_{nom_document.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab5:
            try:
                pdf_bytes = generer_pdf(result, nom_document)
                st.download_button(
                    label="📄 Télécharger rapport PDF",
                    data=pdf_bytes,
                    file_name=f"analyse_{nom_document.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")