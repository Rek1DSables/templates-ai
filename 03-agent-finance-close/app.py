# app.py
import json
import time
import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from graph import build_graph
from config import TYPES_CLOTURE, DEVISES, NORMES


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


def generer_pdf(result: dict, entreprise: str, periode: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"RAPPORT DE CLOTURE — {entreprise.upper()}"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Periode : {periode} | Score qualite : {result['score_qualite']}/100"))
    pdf.multi_cell(largeur, 6, nettoyer(f"Date generation : {time.strftime('%d/%m/%Y %H:%M')}"))
    pdf.ln(4)

    # Rapport narratif
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("RAPPORT NARRATIF"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["rapport_final"].split("\n"):
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

    # Audit log
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("JOURNAL D'AUDIT"))
    pdf.set_font("Helvetica", size=9)
    for entry in result["audit_log"]:
        pdf.multi_cell(largeur, 5, nettoyer(
            f"[{entry.get('timestamp')}] {entry.get('agent')} — {entry.get('etape')} — {entry.get('detail', '')}"
        ))

    return bytes(pdf.output())


# Données de demo
COMPTES_DEMO = [
    {"numero": "411", "libelle": "Clients", "solde_gl": 285000, "solde_auxiliaire": 284200},
    {"numero": "401", "libelle": "Fournisseurs", "solde_gl": 142500, "solde_auxiliaire": 143000},
    {"numero": "512", "libelle": "Banque principale", "solde_gl": 98750, "solde_auxiliaire": 98750},
    {"numero": "701", "libelle": "Ventes produits", "solde_gl": 475000, "solde_auxiliaire": 475000},
    {"numero": "607", "libelle": "Achats marchandises", "solde_gl": 198000, "solde_auxiliaire": 197500},
    {"numero": "641", "libelle": "Salaires", "solde_gl": 87500, "solde_auxiliaire": 87500},
    {"numero": "613", "libelle": "Loyers", "solde_gl": 24000, "solde_auxiliaire": 24000},
    {"numero": "445", "libelle": "TVA collectée", "solde_gl": 95000, "solde_auxiliaire": 94800},
]

TRANSACTIONS_DEMO = [
    {"date": "2026-05-28", "compte": "411", "libelle": "Facture CLI-2026-089", "montant": 15000, "statut": "non_lettree"},
    {"date": "2026-05-29", "compte": "401", "libelle": "Facture FOUR-2026-234", "montant": 8500, "statut": "lettree"},
    {"date": "2026-05-27", "compte": "512", "libelle": "Virement client Acme", "montant": 25000, "statut": "lettree"},
    {"date": "2026-05-26", "compte": "401", "libelle": "Facture FOUR-2026-198 (doublon?)", "montant": 1500, "statut": "suspendue"},
    {"date": "2026-05-25", "compte": "445", "libelle": "TVA décaissée", "montant": -32000, "statut": "lettree"},
]

BUDGET_DEMO = {
    "Chiffre_affaires": 500000,
    "Achats": 200000,
    "Salaires": 85000,
    "Loyers": 24000,
    "Autres_charges": 45000,
    "EBITDA": 146000,
}

REEL_DEMO = {
    "Chiffre_affaires": 475000,
    "Achats": 198000,
    "Salaires": 87500,
    "Loyers": 24000,
    "Autres_charges": 48000,
    "EBITDA": 117500,
}


# --- UI ---
st.set_page_config(page_title="Agent Finance Close", page_icon="📒", layout="centered")
st.title("📒 Agent Finance Close")
st.caption("Pipeline multi-agents de clôture financière — Réconciliation • Variance • Journal Entries • Disclosure • Audit Trail")

st.subheader("Paramètres de clôture")

col1, col2 = st.columns(2)
with col1:
    entreprise = st.text_input("Entreprise", placeholder="Acme Corp SAS")
    type_cloture = st.selectbox("Type de clôture", TYPES_CLOTURE)
    norme = st.selectbox("Norme comptable", NORMES)
with col2:
    periode = st.text_input("Période", placeholder="Mai 2026")
    devise = st.selectbox("Devise", DEVISES)

mode_demo = st.toggle("Mode démo (données pré-remplies)", value=True)

if mode_demo:
    comptes = COMPTES_DEMO
    transactions = TRANSACTIONS_DEMO
    budget = BUDGET_DEMO
    reel = REEL_DEMO
    st.info("Mode démo activé — données fictives Acme Corp SAS.")
else:
    st.subheader("Comptes à réconcilier")
    st.caption("Format : Numéro | Libellé | Solde GL | Solde Auxiliaire")
    nb_comptes = st.number_input("Nombre de comptes", min_value=1, max_value=20, value=4)
    comptes = []
    for i in range(nb_comptes):
        c1, c2, c3, c4 = st.columns([1, 2, 1, 1])
        numero = c1.text_input(f"N° #{i+1}", placeholder="411")
        libelle = c2.text_input(f"Libellé #{i+1}", placeholder="Clients")
        solde_gl = c3.number_input(f"GL #{i+1}", value=0.0)
        solde_aux = c4.number_input(f"Aux #{i+1}", value=0.0)
        comptes.append({"numero": numero, "libelle": libelle, "solde_gl": solde_gl, "solde_auxiliaire": solde_aux})

    st.subheader("Budget vs Réel")
    col_b, col_r = st.columns(2)
    with col_b:
        st.markdown("**Budget**")
        ca_b = st.number_input("CA Budget", value=500000.0)
        charges_b = st.number_input("Charges Budget", value=350000.0)
        budget = {"Chiffre_affaires": ca_b, "Charges_totales": charges_b, "EBITDA": ca_b - charges_b}
    with col_r:
        st.markdown("**Réel**")
        ca_r = st.number_input("CA Réel", value=475000.0)
        charges_r = st.number_input("Charges Réel", value=357500.0)
        reel = {"Chiffre_affaires": ca_r, "Charges_totales": charges_r, "EBITDA": ca_r - charges_r}

    transactions = []

if st.button("Lancer la clôture", use_container_width=True):
    if not entreprise or not periode:
        st.error("Merci de renseigner l'entreprise et la période.")
    else:
        progress = st.progress(0, text="Initialisation...")

        with st.spinner("Pipeline de clôture en cours — 5 agents..."):
            try:
                progress.progress(10, text="Agent Réconciliation en cours...")
                graph = build_graph()
                result = graph.invoke({
                    "entreprise": entreprise,
                    "type_cloture": type_cloture,
                    "periode": periode,
                    "norme": norme,
                    "devise": devise,
                    "comptes": comptes,
                    "transactions": transactions,
                    "budget": budget,
                    "reel": reel,
                    "entites": [],
                    "reconciliations": [],
                    "variances": [],
                    "journal_entries": [],
                    "anomalies": [],
                    "disclosure": "",
                    "rapport_final": "",
                    "score_qualite": 0,
                    "audit_log": [],
                    "erreur": "",
                })
                progress.progress(100, text="Clôture terminée.")
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_qualite"]
        couleur = "🔴" if score < 50 else "🟠" if score < 70 else "🟡" if score < 85 else "🟢"

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score qualité", f"{couleur} {score}/100")
        col2.metric("Réconciliations", len(result["reconciliations"]))
        col3.metric("Anomalies", len(result["anomalies"]))
        col4.metric("Écritures générées", len(result["journal_entries"]))

        anomalies_critiques = [a for a in result["anomalies"] if a.get("niveau") in ["critique", "eleve"]]
        if anomalies_critiques:
            st.error(f"🚨 {len(anomalies_critiques)} anomalie(s) critique(s) détectée(s) — validation manuelle requise")

        st.divider()

        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "Réconciliation",
            "Variances",
            "Journal Entries",
            "Rapport narratif",
            "Audit Trail",
            "Export",
        ])

        with tab1:
            if result["reconciliations"]:
                df_recon = pd.DataFrame(result["reconciliations"])
                st.dataframe(df_recon, use_container_width=True, hide_index=True)
            if result["anomalies"]:
                st.subheader("⚠️ Anomalies détectées")
                for a in result["anomalies"]:
                    niveau = a.get("niveau", "normal")
                    icone = "🔴" if niveau == "critique" else "🟠" if niveau == "eleve" else "🟡"
                    with st.expander(f"{icone} {a.get('type')} — Compte {a.get('compte')}"):
                        st.markdown(f"**Montant :** {a.get('montant')} {devise}")
                        st.markdown(f"**Description :** {a.get('description')}")

        with tab2:
            if result["variances"]:
                df_var = pd.DataFrame(result["variances"])
                if "ecart_pct" in df_var.columns and "poste" in df_var.columns:
                    fig = px.bar(
                        df_var,
                        x="poste",
                        y="ecart_pct",
                        title="Écarts Budget vs Réel (%)",
                        color="ecart_pct",
                        color_continuous_scale="RdYlGn",
                    )
                    st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_var, use_container_width=True, hide_index=True)

        with tab3:
            if result["journal_entries"]:
                for je in result["journal_entries"]:
                    auto_rev = "🔄 Auto-reverse" if je.get("auto_reverse") else ""
                    approuve = "✅ Approuvé" if je.get("approuve") else "⏳ En attente"
                    with st.expander(f"{je.get('reference')} — {je.get('libelle')} {auto_rev}"):
                        col_d, col_c = st.columns(2)
                        col_d.markdown(f"**Débit :** {je.get('debit', {}).get('compte')} {je.get('debit', {}).get('libelle')} — {je.get('debit', {}).get('montant')} {devise}")
                        col_c.markdown(f"**Crédit :** {je.get('credit', {}).get('compte')} {je.get('credit', {}).get('libelle')} — {je.get('credit', {}).get('montant')} {devise}")
                        st.markdown(f"**Statut :** {approuve} | **Date :** {je.get('date')} | **Type :** {je.get('type')}")

        with tab4:
            st.markdown(result["rapport_final"])

        with tab5:
            st.caption("Journal d'audit complet horodaté — traçabilité de toutes les décisions agents")
            for entry in result["audit_log"]:
                statut = entry.get("statut", "")
                icone = "✅" if statut == "complete" else "⏳"
                st.markdown(f"{icone} `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

            st.divider()
            json_log = json.dumps(result["audit_log"], ensure_ascii=False, indent=2)
            st.download_button(
                label="📦 Télécharger Audit Log JSON",
                data=json_log,
                file_name=f"audit_log_{entreprise.replace(' ', '_')}_{periode.replace(' ', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab6:
            col_pdf, col_json = st.columns(2)
            with col_pdf:
                try:
                    pdf_bytes = generer_pdf(result, entreprise, periode)
                    st.download_button(
                        label="📄 Télécharger rapport PDF",
                        data=pdf_bytes,
                        file_name=f"cloture_{entreprise.replace(' ', '_')}_{periode.replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"PDF indisponible : {e}")
            with col_json:
                export = {
                    "entreprise": entreprise,
                    "periode": periode,
                    "score_qualite": result["score_qualite"],
                    "reconciliations": result["reconciliations"],
                    "variances": result["variances"],
                    "journal_entries": result["journal_entries"],
                    "anomalies": result["anomalies"],
                    "audit_log": result["audit_log"],
                }
                st.download_button(
                    label="📦 Télécharger données JSON",
                    data=json.dumps(export, ensure_ascii=False, indent=2),
                    file_name=f"cloture_{entreprise.replace(' ', '_')}_{periode.replace(' ', '_')}.json",
                    mime="application/json",
                    use_container_width=True,
                )