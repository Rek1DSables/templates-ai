# app.py
import json
import time
import streamlit as st
from fpdf import FPDF
from graph import build_graph
from config import (
    SECTEURS, CATEGORIES_RISQUE_ELEVE,
    NIVEAUX_RISQUE, DEADLINES, ARTICLES_EU_AI_ACT
)


def nettoyer(texte: str) -> str:
    remplacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201c": '"', "\u201d": '"',
        "\u00ab": '"', "\u00bb": '"',
        "\u2013": "-", "\u2014": "-",
        "\u2026": "...", "\u00a0": " ",
        "\u2713": "OK", "\u2714": "OK",
        "\u2715": "KO", "\u2716": "KO",
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


def generer_pdf(result: dict, nom_systeme: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    # En-tete
    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"RAPPORT AUDIT EU AI ACT — {nom_systeme.upper()}"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Date : {time.strftime('%d/%m/%Y')} | Score conformite : {result['score_conformite']}/100"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Niveau risque : {result['classification'].get('niveau_risque', '—')}"))
    pdf.ln(4)

    # Classification
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("CLASSIFICATION EU AI ACT"))
    pdf.set_font("Helvetica", size=10)
    classif = result["classification"]
    pdf.multi_cell(largeur, 6, nettoyer(f"Justification : {classif.get('justification', '—')}"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Articles applicables : {', '.join(classif.get('articles_applicables', []))}"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Est GPAI : {'Oui' if classif.get('est_gpai') else 'Non'}"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Pratiques interdites : {'Oui' if classif.get('pratiques_interdites') else 'Non'}"))
    pdf.ln(4)

    # Analyse articles
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("ANALYSE PAR ARTICLE"))
    pdf.set_font("Helvetica", size=10)
    for article, data in result["analyse_articles"].items():
        statut = data.get("statut", "—")
        score = data.get("score", 0)
        pdf.set_font("Helvetica", style="B", size=10)
        pdf.multi_cell(largeur, 6, nettoyer(f"{article} : {statut} ({score}/100)"))
        pdf.set_font("Helvetica", size=10)
        for gap in data.get("gaps", [])[:2]:
            pdf.multi_cell(largeur, 6, nettoyer(f"  Gap : {gap}"))
        pdf.ln(2)

    # Plan de remediation
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("PLAN DE REMEDIATION"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["plan_remediation"].split("\n"):
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

    # Audit trail
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("JOURNAL D'AUDIT (AUDIT TRAIL)"))
    pdf.set_font("Helvetica", size=9)
    for entry in result["audit_trail"]:
        pdf.multi_cell(largeur, 5, nettoyer(
            f"[{entry.get('timestamp', '')}] {entry.get('etape', '')} — {entry.get('statut', '')} — {entry.get('resultat', '')}"
        ))

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent EU AI Act Compliance", page_icon="⚖️", layout="centered")
st.title("⚖️ Agent EU AI Act Compliance")
st.caption("Audit de conformité EU AI Act — Classification, analyse par article, plan de remédiation, audit trail")

# Bandeau deadlines
with st.expander("📅 Deadlines EU AI Act — À ne pas manquer"):
    for deadline, desc in DEADLINES.items():
        st.markdown(f"**{deadline}** : {desc}")

st.divider()
st.subheader("Informations sur le système IA à auditer")

col1, col2 = st.columns(2)
with col1:
    nom_systeme = st.text_input("Nom du système IA", placeholder="RecrutAI Pro")
    secteur = st.selectbox("Secteur d'activité", SECTEURS)
    categorie_risque = st.selectbox("Catégorie déclarée (Annexe III)", CATEGORIES_RISQUE_ELEVE)

with col2:
    utilisateurs = st.text_input("Utilisateurs finaux", placeholder="Responsables RH, 500 utilisateurs en France et UE")
    donnees_traitees = st.text_area("Données traitées", placeholder="CV, profils LinkedIn, données biographiques, scores IA", height=80)

description = st.text_area(
    "Description du système",
    placeholder="Système d'IA qui analyse automatiquement les CV et profils de candidats, attribue un score de compatibilité et classe les candidats par ordre de pertinence. Utilisé pour présélectionner les candidats avant entretien.",
    height=100,
)

usages = st.text_area(
    "Usages et cas d'usage",
    placeholder="Présélection automatique des CV, scoring de candidats, classement automatique, recommandation de candidats à l'équipe RH",
    height=80,
)

st.divider()

if st.button("Lancer l'audit EU AI Act", use_container_width=True):
    if not nom_systeme or not description:
        st.error("Merci de renseigner le nom et la description du système.")
    else:
        progress = st.progress(0, text="Initialisation de l'audit...")

        with st.spinner("Audit EU AI Act en cours — 5 étapes..."):
            try:
                progress.progress(10, text="Classification du système...")
                graph = build_graph()
                result = graph.invoke({
                    "nom_systeme": nom_systeme,
                    "description": description,
                    "secteur": secteur,
                    "categorie_risque": categorie_risque,
                    "usages": usages,
                    "donnees_traitees": donnees_traitees,
                    "utilisateurs": utilisateurs,
                    "classification": {},
                    "analyse_articles": {},
                    "gaps": [],
                    "plan_remediation": "",
                    "score_conformite": 0,
                    "audit_trail": [],
                    "erreur": "",
                })
                progress.progress(100, text="Audit terminé.")
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        # Métriques principales
        score = result["score_conformite"]
        niveau = result["classification"].get("niveau_risque", "—")
        couleur_score = "🔴" if score < 40 else "🟠" if score < 60 else "🟡" if score < 80 else "🟢"
        couleur_niveau = "🔴" if niveau == "Inacceptable" else "🟠" if niveau == "Élevé" else "🟡" if niveau == "Limité" else "🟢"

        col1, col2, col3 = st.columns(3)
        col1.metric("Score de conformité", f"{couleur_score} {score}/100")
        col2.metric("Niveau de risque", f"{couleur_niveau} {niveau}")
        col3.metric("Gaps identifiés", len(result["gaps"]))

        # Flags critiques
        flags = result["classification"].get("flags_critiques", [])
        if flags:
            st.error(f"🚨 Flags critiques : {' | '.join(flags)}")

        # Pratiques interdites
        if result["classification"].get("pratiques_interdites"):
            st.error("🔴 ALERTE : Des pratiques potentiellement interdites (Article 5) ont été détectées. Consultation juridique immédiate requise.")

        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Classification",
            "Analyse par article",
            "Plan de remédiation",
            "Audit Trail",
            "Export PDF",
        ])

        with tab1:
            classif = result["classification"]
            st.markdown(f"**Niveau de risque :** {couleur_niveau} {classif.get('niveau_risque')}")
            st.markdown(f"**Justification :** {classif.get('justification')}")
            st.markdown(f"**Articles applicables :** {', '.join(classif.get('articles_applicables', []))}")
            st.markdown(f"**Système GPAI :** {'Oui' if classif.get('est_gpai') else 'Non'}")
            st.markdown(f"**Catégorie Annexe III :** {classif.get('categorie_annexe_iii', 'N/A')}")
            st.markdown(f"**Score de risque initial :** {classif.get('score_risque_initial')}/100")

        with tab2:
            import pandas as pd
            rows = []
            for article, data in result["analyse_articles"].items():
                statut = data.get("statut", "—")
                icone = "✅" if statut == "conforme" else "⚠️" if statut == "partiel" else "❌" if statut == "non_conforme" else "➖"
                rows.append({
                    "Article": article.split(" — ")[0],
                    "Statut": f"{icone} {statut}",
                    "Score": f"{data.get('score', 0)}/100",
                    "Gaps": len(data.get("gaps", [])),
                })
            if rows:
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            for article, data in result["analyse_articles"].items():
                statut = data.get("statut", "—")
                icone = "✅" if statut == "conforme" else "⚠️" if statut == "partiel" else "❌"
                with st.expander(f"{icone} {article} — Score {data.get('score', 0)}/100"):
                    if data.get("constats"):
                        st.markdown("**Constats :**")
                        for c in data["constats"]:
                            st.markdown(f"- {c}")
                    if data.get("gaps"):
                        st.markdown("**Gaps :**")
                        for g in data["gaps"]:
                            st.warning(g)
                    if data.get("actions_requises"):
                        st.markdown("**Actions requises :**")
                        for a in data["actions_requises"]:
                            st.markdown(f"→ {a}")

        with tab3:
            st.markdown(result["plan_remediation"])

        with tab4:
            st.caption("Journal complet de toutes les étapes de l'audit — conforme aux exigences EU AI Act Article 17")
            audit_trail = result["audit_trail"]
            for entry in audit_trail:
                statut = entry.get("statut", "")
                icone = "✅" if statut == "complete" else "⏳"
                st.markdown(
                    f"{icone} `{entry.get('timestamp', '')}` **{entry.get('etape', '')}** — {entry.get('resultat', statut)}"
                )

            st.divider()
            json_trail = json.dumps(audit_trail, ensure_ascii=False, indent=2)
            st.download_button(
                label="📦 Télécharger Audit Trail JSON",
                data=json_trail,
                file_name=f"audit_trail_{nom_systeme.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab5:
            try:
                pdf_bytes = generer_pdf(result, nom_systeme)
                st.download_button(
                    label="📄 Télécharger rapport PDF complet",
                    data=pdf_bytes,
                    file_name=f"audit_eu_ai_act_{nom_systeme.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")