# app.py
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import date
from fpdf import FPDF
from supabase import create_client
from graph import build_graph
from config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_TABLE, SECTEURS, PERIODES

# Init Supabase
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.warning(f"Supabase non connecte : {e}")


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


def generer_pdf(result: dict, entreprise: str, secteur: str, periode: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer("RAPPORT DE PERFORMANCE"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Entreprise : {entreprise} | Secteur : {secteur} | Periode : {periode}"))
    pdf.multi_cell(largeur, 8, nettoyer(f"Score de sante : {result['score_sante']}/100 | Date : {str(date.today())}"))
    pdf.ln(4)

    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("ANALYSE DES KPIS"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["analyse_kpis"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        pdf.multi_cell(largeur, 6, ligne)
    pdf.ln(4)

    if result["tendances"]:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 8, nettoyer("TENDANCES"))
        pdf.set_font("Helvetica", size=10)
        for t in result["tendances"]:
            pdf.multi_cell(largeur, 6, nettoyer(f"+ {t}"))
        pdf.ln(4)

    if result["alertes"]:
        pdf.set_font("Helvetica", style="B", size=12)
        pdf.multi_cell(largeur, 8, nettoyer("ALERTES"))
        pdf.set_font("Helvetica", size=10)
        for a in result["alertes"]:
            pdf.multi_cell(largeur, 6, nettoyer(f"! {a}"))
        pdf.ln(4)

    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 8, nettoyer("RECOMMANDATIONS"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result["recommandations"].split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


def sauvegarder_supabase(data: dict):
    if not supabase:
        return
    try:
        supabase.table(SUPABASE_TABLE).insert(data).execute()
    except Exception as e:
        st.warning(f"Erreur Supabase : {e}")


# --- UI ---
st.set_page_config(page_title="Dashboard Reporting AI", page_icon="📊", layout="wide")
st.title("📊 Dashboard Reporting & Analytics AI")
st.caption("Saisie des KPIs → Analyse Claude → Dashboard Plotly → Rapport PDF")

with st.sidebar:
    st.subheader("Configuration")
    entreprise = st.text_input("Entreprise", placeholder="Acme Corp")
    secteur = st.selectbox("Secteur", SECTEURS)
    periode = st.selectbox("Periode", PERIODES)

    st.subheader("KPIs")
    st.caption("Saisis tes indicateurs cles (nom : valeur)")

    kpi_data = {}
    kpis_defaut = [
        ("Chiffre d'affaires (EUR)", "125000"),
        ("Croissance CA (%)", "12"),
        ("Nouveaux clients", "45"),
        ("Taux de churn (%)", "3.2"),
        ("MRR (EUR)", "42000"),
        ("NPS", "67"),
        ("Cout acquisition client (EUR)", "320"),
        ("Taux conversion (%)", "4.5"),
    ]

    for nom, valeur_defaut in kpis_defaut:
        val = st.text_input(nom, value=valeur_defaut)
        if val:
            kpi_data[nom] = val

    kpi_custom1_nom = st.text_input("KPI custom 1 (nom)", placeholder="Tickets resolus")
    kpi_custom1_val = st.text_input("KPI custom 1 (valeur)", placeholder="234")
    if kpi_custom1_nom and kpi_custom1_val:
        kpi_data[kpi_custom1_nom] = kpi_custom1_val

    kpi_custom2_nom = st.text_input("KPI custom 2 (nom)", placeholder="Taux satisfaction (%)")
    kpi_custom2_val = st.text_input("KPI custom 2 (valeur)", placeholder="92")
    if kpi_custom2_nom and kpi_custom2_val:
        kpi_data[kpi_custom2_nom] = kpi_custom2_val

    lancer = st.button("Generer le rapport", use_container_width=True)

if lancer:
    if not entreprise or not kpi_data:
        st.error("Merci de remplir le nom de l'entreprise et au moins un KPI.")
    else:
        with st.spinner("Analyse des KPIs en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "entreprise": entreprise,
                    "secteur": secteur,
                    "periode": periode,
                    "kpis": kpi_data,
                    "analyse_kpis": "",
                    "tendances": [],
                    "alertes": [],
                    "recommandations": "",
                    "score_sante": 0,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")

        # Score sante
        score = result["score_sante"]
        couleur = "green" if score >= 70 else "orange" if score >= 40 else "red"

        col1, col2, col3 = st.columns(3)
        col1.metric("Entreprise", entreprise)
        col2.metric("Periode", periode)
        col3.metric("Score de sante", f"{score}/100")

        st.divider()

        # Gauge score
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Score de sante global"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": couleur},
                "steps": [
                    {"range": [0, 40], "color": "#ffcccc"},
                    {"range": [40, 70], "color": "#fff3cc"},
                    {"range": [70, 100], "color": "#ccffcc"},
                ],
            }
        ))
        fig_gauge.update_layout(height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)

        # KPIs bar chart
        kpi_noms = list(kpi_data.keys())
        kpi_vals = []
        for v in kpi_data.values():
            try:
                kpi_vals.append(float(v.replace(",", ".").replace("%", "").replace("EUR", "").strip()))
            except:
                kpi_vals.append(0)

        fig_bar = px.bar(
            x=kpi_noms,
            y=kpi_vals,
            title=f"KPIs — {entreprise} — {periode}",
            labels={"x": "KPI", "y": "Valeur"},
            color=kpi_vals,
            color_continuous_scale="Blues",
        )
        fig_bar.update_layout(height=350, showlegend=False)
        st.plotly_chart(fig_bar, use_container_width=True)

        st.divider()

        tab1, tab2, tab3 = st.tabs(["Analyse & Recommandations", "Tendances & Alertes", "Export"])

        with tab1:
            st.subheader("Analyse des KPIs")
            st.markdown(result["analyse_kpis"])
            st.subheader("Recommandations")
            st.markdown(result["recommandations"])

        with tab2:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Tendances")
                for t in result["tendances"]:
                    st.success(f"↗ {t}")
            with col2:
                st.subheader("Alertes")
                for a in result["alertes"]:
                    st.warning(f"⚠ {a}")

        with tab3:
            try:
                pdf_bytes = generer_pdf(result, entreprise, secteur, periode)
                st.download_button(
                    label="Telecharger le rapport PDF",
                    data=pdf_bytes,
                    file_name=f"rapport_{entreprise.replace(' ', '_')}_{periode}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"Export PDF indisponible : {e}")

        sauvegarder_supabase({
            "entreprise": entreprise,
            "secteur": secteur,
            "periode": periode,
            "kpis": str(kpi_data),
            "score_sante": score,
            "tendances": "\n".join(result["tendances"]),
            "alertes": "\n".join(result["alertes"]),
            "recommandations": result["recommandations"],
            "date_rapport": str(date.today()),
        })