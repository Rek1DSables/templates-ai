# app.py
import json
import time
import streamlit as st
import pandas as pd
from fpdf import FPDF
from graph import build_graph
from config import TYPES_CONTRATS, MODES, NIVEAUX_RISQUE, SQL_SETUP

CONTRAT_DEMO = """CONTRAT DE PRESTATION DE SERVICES

Entre les soussignés :
La société INNOVATECH SAS, au capital de 100 000€, RCS Paris 456 789 123, sise 8 rue du Louvre 75001 Paris, représentée par M. Pierre LEBLANC, Directeur Général (ci-après "le Client")

ET

La société DEVPRO SARL, au capital de 15 000€, RCS Lyon 321 654 987, sise 22 cours Gambetta 69003 Lyon, représentée par Mme Claire SIMON, Gérante (ci-après "le Prestataire")

ARTICLE 1 - OBJET
Le Prestataire fournit des services de développement d'agents IA et d'automatisation des processus métier selon les spécifications définies en annexe.

ARTICLE 2 - DURÉE
Contrat conclu pour 12 mois à compter du 1er juin 2026. Renouvellement tacite par périodes de 12 mois sauf préavis de 30 jours.

ARTICLE 3 - PRIX
Tarif journalier : 700€ HT. Paiement à 90 jours fin de mois (dépasse le délai légal LME de 60 jours).

ARTICLE 4 - RESPONSABILITÉ
Le Prestataire est responsable de TOUS les dommages directs ET indirects sans aucune limitation de montant. Le Client n'engage aucune responsabilité quelle que soit sa faute.

ARTICLE 5 - PROPRIÉTÉ INTELLECTUELLE
Toute création réalisée par le Prestataire, y compris ses outils propriétaires et méthodes génériques, devient propriété exclusive du Client.

ARTICLE 6 - RÉSILIATION
Le Client peut résilier sans préavis ni indemnité. Le Prestataire doit respecter 6 mois de préavis même en cas de faute grave du Client.

ARTICLE 7 - CONFIDENTIALITÉ
Durée de confidentialité : 2 ans après la fin du contrat.

ARTICLE 8 - LOI APPLICABLE
Droit français. Tribunaux compétents : Paris."""


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


def generer_pdf(result: dict, nom_contrat: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"PIPELINE CONTRACTUEL — {nom_contrat.upper()}"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Date : {time.strftime('%d/%m/%Y')} | Score risque : {result['score_risque']}/100"))
    pdf.ln(4)

    if result.get("analyse_complete"):
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 8, nettoyer("ANALYSE CONTRACTUELLE"))
        pdf.set_font("Helvetica", size=10)
        for ligne in result["analyse_complete"].split("\n"):
            ligne = nettoyer(ligne.strip())
            if not ligne:
                pdf.ln(2)
                continue
            if ligne.isupper():
                pdf.set_font("Helvetica", style="B", size=11)
                pdf.multi_cell(largeur, 7, ligne)
                pdf.set_font("Helvetica", size=10)
            else:
                pdf.multi_cell(largeur, 6, ligne)
        pdf.ln(4)

    if result.get("contrat_genere"):
        pdf.add_page()
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 8, nettoyer("CONTRAT GÉNÉRÉ"))
        pdf.set_font("Helvetica", size=10)
        for ligne in result["contrat_genere"].split("\n"):
            ligne = nettoyer(ligne.strip())
            if not ligne:
                pdf.ln(2)
                continue
            if ligne.isupper():
                pdf.set_font("Helvetica", style="B", size=11)
                pdf.multi_cell(largeur, 7, ligne)
                pdf.set_font("Helvetica", size=10)
            else:
                pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


st.set_page_config(page_title="Agent Pipeline Contractuel", page_icon="📋", layout="centered")
st.title("📋 Agent Pipeline Contractuel Multi-Agents")
st.caption("Extraction clauses → Analyse risques → Synthèse → Génération contrat amélioré")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Extraction** — extrait et structure toutes les clauses
2. **Agent Analyse Risques** — identifie risques, clauses abusives, illégalités
3. **Agent Synthèse** — verdict, recommandations, actions avant signature
4. **Agent Génération** — contrat amélioré ou nouveau contrat
    """)

with st.expander("🗄️ Setup Supabase"):
    st.code(SQL_SETUP, language="sql")

st.divider()

mode = st.selectbox("Mode", MODES)
type_contrat = st.selectbox("Type de contrat", TYPES_CONTRATS)

contenu_original = ""
nom_contrat = ""
parties = {}
objet = ""
contexte = ""

if mode == "Analyser un contrat existant" or mode == "Analyser ET générer une version améliorée":
    source = st.radio("Source", ["Document de démo", "Coller le texte", "Uploader un PDF"], horizontal=True)

    if source == "Document de démo":
        contenu_original = CONTRAT_DEMO
        nom_contrat = "Contrat Prestation INNOVATECH-DEVPRO"
        type_contrat = "Contrat de prestation de services"
        with st.expander("Aperçu du contrat de démo"):
            st.text(CONTRAT_DEMO[:400] + "...")
    elif source == "Coller le texte":
        nom_contrat = st.text_input("Nom du contrat", placeholder="Contrat XYZ")
        contenu_original = st.text_area("Contenu du contrat", height=250)
    else:
        nom_contrat = st.text_input("Nom du contrat", placeholder="Contrat XYZ")
        fichier = st.file_uploader("Fichier PDF", type=["pdf"])
        if fichier:
            try:
                import pymupdf
                pdf_bytes = fichier.read()
                doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
                contenu_original = "".join([page.get_text() for page in doc])
                st.success(f"PDF extrait : {len(contenu_original)} caractères")
            except Exception as e:
                st.error(f"Erreur : {e}")

else:
    # Mode génération pure
    nom_contrat = st.text_input("Nom du contrat", placeholder="Contrat de prestation IA")
    col1, col2 = st.columns(2)
    with col1:
        partie1_nom = st.text_input("Partie 1 — Nom", placeholder="ACME Corp SAS")
        partie1_siret = st.text_input("Partie 1 — SIRET", placeholder="123 456 789 00010")
    with col2:
        partie2_nom = st.text_input("Partie 2 — Nom", placeholder="DevAgency SARL")
        partie2_siret = st.text_input("Partie 2 — SIRET", placeholder="987 654 321 00015")
    parties = {
        "partie1": {"nom": partie1_nom, "siret": partie1_siret},
        "partie2": {"nom": partie2_nom, "siret": partie2_siret},
    }
    objet = st.text_area("Objet du contrat", placeholder="Développement d'agents IA et automatisation des processus métier")
    contexte = st.text_area("Contexte", placeholder="Mission de 6 mois, tarif 700€/jour, propriété intellectuelle partagée")

if st.button("Lancer le pipeline contractuel", use_container_width=True):
    if not nom_contrat:
        st.error("Merci de renseigner le nom du contrat.")
    elif mode != "Générer un nouveau contrat" and not contenu_original:
        st.error("Merci de fournir le contenu du contrat.")
    else:
        with st.spinner("Pipeline contractuel en cours — 4 agents..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "mode": mode,
                    "type_contrat": type_contrat,
                    "nom_contrat": nom_contrat,
                    "contenu_original": contenu_original,
                    "parties": parties,
                    "objet": objet,
                    "contexte": contexte,
                    "clauses_extraites": {},
                    "clauses_manquantes": [],
                    "risques": [],
                    "score_risque": 0,
                    "analyse_partie1": "",
                    "analyse_partie2": "",
                    "analyse_complete": "",
                    "contrat_genere": "",
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
        col1.metric("Score risque", f"{couleur} {score}/100" if score > 0 else "—")
        col2.metric("Risques identifiés", len(result["risques"]))
        col3.metric("Clauses manquantes", len(result["clauses_manquantes"]))

        if nb_critiques > 0:
            st.error(f"🚨 {nb_critiques} risque(s) CRITIQUE(S) — ne pas signer sans négociation")

        st.divider()

        tabs = []
        tab_labels = []

        if result["analyse_complete"]:
            tab_labels.append("Analyse & Verdict")
        if result["risques"]:
            tab_labels.append("Matrice des risques")
        if result["clauses_extraites"]:
            tab_labels.append("Clauses extraites")
        if result["contrat_genere"]:
            tab_labels.append("Contrat généré")
        tab_labels.extend(["Audit Trail", "Export PDF"])

        tabs = st.tabs(tab_labels)
        tab_idx = 0

        if result["analyse_complete"]:
            with tabs[tab_idx]:
                st.markdown(result["analyse_complete"])
            tab_idx += 1

        if result["risques"]:
            with tabs[tab_idx]:
                for niveau in ["critique", "eleve", "moyen", "faible"]:
                    risques_niveau = [r for r in result["risques"] if r.get("niveau") == niveau]
                    if risques_niveau:
                        icone = NIVEAUX_RISQUE.get(niveau, "🟡")
                        st.subheader(f"{icone} {niveau.capitalize()} ({len(risques_niveau)})")
                        for r in risques_niveau:
                            with st.expander(f"{r.get('titre', 'Risque')}"):
                                st.markdown(f"**Clause :** {r.get('clause_concernee', '')}")
                                st.markdown(f"**Description :** {r.get('description', '')}")
                                st.markdown(f"**Impact :** {r.get('impact', '')}")
                                st.info(f"**Recommandation :** {r.get('recommandation', '')}")
            tab_idx += 1

        if result["clauses_extraites"]:
            with tabs[tab_idx]:
                rows = []
                for clause, valeur in result["clauses_extraites"].items():
                    rows.append({
                        "Clause": clause,
                        "Présente": "✅" if valeur else "❌",
                        "Contenu": str(valeur or "—")[:100],
                    })
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
                if result["clauses_manquantes"]:
                    st.warning(f"Clauses manquantes : {', '.join(result['clauses_manquantes'])}")
            tab_idx += 1

        if result["contrat_genere"]:
            with tabs[tab_idx]:
                st.markdown(result["contrat_genere"])
            tab_idx += 1

        with tabs[tab_idx]:
            for entry in result["audit_log"]:
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")
            st.download_button(
                label="📦 Audit Trail JSON",
                data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
                file_name=f"audit_{nom_contrat.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )
        tab_idx += 1

        with tabs[tab_idx]:
            try:
                pdf_bytes = generer_pdf(result, nom_contrat)
                st.download_button(
                    label="📄 Télécharger rapport PDF",
                    data=pdf_bytes,
                    file_name=f"contrat_{nom_contrat.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")