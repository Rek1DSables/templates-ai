# app.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from fpdf import FPDF
from graph import build_graph
from config import SECTEURS, PERIODES


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
    pdf.multi_cell(largeur, 10, nettoyer(f"RAPPORT {periode.upper()} — {entreprise}"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Score de sante : {result['score_sante']}/100"))
    pdf.ln(4)

    sections = [
        ("ANALYSE KPIs", result["analyse_kpis"]),
        ("TENDANCES", "\n".join(f"- {t}" for t in result["tendances"])),
        ("ALERTES", "\n".join(f"- {a}" for a in result["alertes"])),
        ("RECOMMANDATIONS", result["recommandations"]),
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
            pdf.multi_cell(largeur, 6, ligne)
        pdf.ln(4)

    return bytes(pdf.output())


# --- UI ---
st.set_page_config(page_title="Agent Reporting & Alertes", page_icon="📊", layout="centered")
st.title("📊 Agent Reporting & Alertes")
st.caption("Analyse KPIs + Recommandations + Alertes + Export PDF + Envoi email")

with st.form("form_reporting"):
    col1, col2 = st.columns(2)
    with col1:
        entreprise = st.text_input("Entreprise", placeholder="Acme Corp")
        secteur = st.selectbox("Secteur", SECTEURS)
    with col2:
        periode = st.selectbox("Période", PERIODES)

    st.subheader("KPIs")
    st.caption("Renseigne les valeurs de tes indicateurs clés")

    col_a, col_b = st.columns(2)
    with col_a:
        ca = st.number_input("Chiffre d'affaires (EUR)", min_value=0.0, value=125000.0)
        croissance = st.number_input("Croissance (%)", min_value=-100.0, value=12.0)
        nouveaux_clients = st.number_input("Nouveaux clients", min_value=0, value=45)
        taux_conversion = st.number_input("Taux de conversion (%)", min_value=0.0, value=4.5)
    with col_b:
        mrr = st.number_input("MRR (EUR)", min_value=0.0, value=42000.0)
        churn = st.number_input("Taux de churn (%)", min_value=0.0, value=3.2)
        nps = st.number_input("NPS", min_value=-100, max_value=100, value=67)
        cac = st.number_input("CAC (EUR)", min_value=0.0, value=320.0)

    st.divider()
    st.subheader("Envoi email (optionnel)")
    envoyer_email = st.checkbox("Envoyer le rapport par email")
    destinataire_email = ""
    if envoyer_email:
        destinataire_email = st.text_input("Email destinataire", placeholder="direction@acme.com")

    submit = st.form_submit_button("Générer le rapport", use_container_width=True)

if submit:
    if not entreprise:
        st.error("Merci de renseigner le nom de l'entreprise.")
    else:
        with st.spinner("Analyse en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "entreprise": entreprise,
                    "secteur": secteur,
                    "periode": periode,
                    "kpis": {
                        "Chiffre d affaires": f"{ca} EUR",
                        "Croissance": f"{croissance}%",
                        "Nouveaux clients": nouveaux_clients,
                        "Taux de conversion": f"{taux_conversion}%",
                        "MRR": f"{mrr} EUR",
                        "Taux de churn": f"{churn}%",
                        "NPS": nps,
                        "CAC": f"{cac} EUR",
                    },
                    "analyse_kpis": "",
                    "tendances": [],
                    "alertes": [],
                    "recommandations": "",
                    "score_sante": 0,
                    "envoyer_email": envoyer_email,
                    "destinataire_email": destinataire_email,
                    "rapport_pdf": True,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_sante"]
        couleur = "🔴" if score < 40 else "🟠" if score < 60 else "🟡" if score < 80 else "🟢"

        col1, col2, col3 = st.columns(3)
        col1.metric("Entreprise", entreprise)
        col2.metric("Période", periode)
        col3.metric("Score de santé", f"{couleur} {score}/100")

        st.divider()

        # Dashboard KPIs
        fig = go.Figure()
        kpis_numeriques = {
            "CA (kEUR)": ca / 1000,
            "Croissance (%)": croissance,
            "Conv. (%)": taux_conversion,
            "Churn (%)": churn,
            "NPS": nps / 10,
            "MRR (kEUR)": mrr / 1000,
        }
        fig = px.bar(
            x=list(kpis_numeriques.keys()),
            y=list(kpis_numeriques.values()),
            title="Vue d'ensemble des KPIs",
            color=list(kpis_numeriques.values()),
            color_continuous_scale="RdYlGn",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Alertes
        if result["alertes"]:
            st.subheader("⚠️ Alertes")
            for alerte in result["alertes"]:
                st.warning(alerte)

        tab1, tab2, tab3 = st.tabs(["Analyse & Recommandations", "Tendances", "Export"])

        with tab1:
            st.markdown("**Analyse des KPIs**")
            st.markdown(result["analyse_kpis"])
            st.divider()
            st.markdown("**Recommandations**")
            st.markdown(result["recommandations"])

        with tab2:
            for t in result["tendances"]:
                st.markdown(f"📈 {t}")

        with tab3:
            try:
                pdf_bytes = generer_pdf(result, entreprise, periode)
                st.download_button(
                    label="📄 Télécharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"rapport_{entreprise.replace(' ', '_')}_{periode}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"PDF indisponible : {e}")

        if envoyer_email and destinataire_email and not result["erreur"]:
            st.success(f"Rapport envoyé à {destinataire_email}")