# app.py
import json
import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fpdf import FPDF
from graph import build_graph
from config import TYPES_ANALYSE


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


def generer_pdf(result: dict, nom_fichier: str, type_analyse: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_left_margin(20)
    pdf.set_right_margin(20)
    largeur = pdf.w - pdf.l_margin - pdf.r_margin

    pdf.set_font("Helvetica", style="B", size=14)
    pdf.multi_cell(largeur, 10, nettoyer(f"RAPPORT D'ANALYSE — {nom_fichier}"))
    pdf.set_font("Helvetica", size=11)
    pdf.multi_cell(largeur, 8, nettoyer(f"Type : {type_analyse}"))
    pdf.ln(4)

    stats = result.get("statistiques", {})
    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 9, nettoyer("STATISTIQUES CLES"))
    pdf.set_font("Helvetica", size=10)
    pdf.multi_cell(largeur, 6, nettoyer(f"Lignes : {stats.get('nb_lignes', '—')} | Colonnes : {stats.get('nb_colonnes', '—')} | Qualite donnees : {stats.get('qualite_donnees', '—')}/100"))
    pdf.ln(4)

    pdf.set_font("Helvetica", style="B", size=12)
    pdf.multi_cell(largeur, 9, nettoyer("INSIGHTS ET RECOMMANDATIONS"))
    pdf.set_font("Helvetica", size=10)
    for ligne in result.get("insights", "").split("\n"):
        ligne = nettoyer(ligne.strip())
        if not ligne:
            pdf.ln(3)
            continue
        if ligne.isupper() or ligne.startswith("#"):
            pdf.set_font("Helvetica", style="B", size=11)
            pdf.multi_cell(largeur, 8, ligne.replace("#", "").strip())
            pdf.set_font("Helvetica", size=10)
        else:
            pdf.multi_cell(largeur, 6, ligne)

    return bytes(pdf.output())


def auto_visualisations(df: pd.DataFrame) -> list:
    charts = []
    numeriques = df.select_dtypes(include=["number"]).columns.tolist()
    categories = df.select_dtypes(include=["object"]).columns.tolist()

    if len(numeriques) >= 2:
        fig = px.scatter(df, x=numeriques[0], y=numeriques[1],
                        title=f"{numeriques[0]} vs {numeriques[1]}")
        charts.append(fig)

    if len(numeriques) >= 1:
        fig = px.histogram(df, x=numeriques[0],
                          title=f"Distribution — {numeriques[0]}")
        charts.append(fig)

    if len(categories) >= 1 and len(numeriques) >= 1:
        top = df.groupby(categories[0])[numeriques[0]].sum().nlargest(10).reset_index()
        fig = px.bar(top, x=categories[0], y=numeriques[0],
                    title=f"{numeriques[0]} par {categories[0]} (Top 10)")
        charts.append(fig)

    if len(numeriques) >= 3:
        fig = px.imshow(df[numeriques].corr(),
                       title="Matrice de corrélation",
                       color_continuous_scale="RdBu")
        charts.append(fig)

    return charts


# --- UI ---
st.set_page_config(page_title="Agent Analyse de Données", page_icon="📈", layout="centered")
st.title("📈 Agent Analyse de Données")
st.caption("Upload CSV/Excel → Analyse statistique → Insights IA → Visualisations → Rapport PDF")

type_analyse = st.selectbox("Type d'analyse", TYPES_ANALYSE)
contexte = st.text_input(
    "Contexte business (optionnel)",
    placeholder="Ex : données de ventes e-commerce Q1 2026, objectif : identifier les produits sous-performants"
)

fichier = st.file_uploader("Upload CSV ou Excel", type=["csv", "xlsx", "xls"])

if fichier:
    try:
        if fichier.name.endswith(".csv"):
            df = pd.read_csv(fichier)
        else:
            df = pd.read_excel(fichier)

        st.success(f"Fichier chargé : {df.shape[0]} lignes × {df.shape[1]} colonnes")

        with st.expander("Aperçu des données"):
            st.dataframe(df.head(10), use_container_width=True)

    except Exception as e:
        st.error(f"Erreur lecture fichier : {e}")
        st.stop()

    if st.button("Analyser", use_container_width=True):
        donnees_brutes = df.to_string(max_rows=100)

        with st.spinner("Analyse en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_analyse": type_analyse,
                    "nom_fichier": fichier.name,
                    "contexte": contexte,
                    "donnees_brutes": donnees_brutes,
                    "statistiques": {},
                    "insights": "",
                    "recommandations": "",
                    "alertes": [],
                    "visualisations": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        stats = result["statistiques"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Lignes", stats.get("nb_lignes", df.shape[0]))
        col2.metric("Colonnes", stats.get("nb_colonnes", df.shape[1]))
        col3.metric("Qualité données", f"{stats.get('qualite_donnees', '—')}/100")

        if result["alertes"]:
            st.subheader("⚠️ Alertes")
            for alerte in result["alertes"]:
                st.warning(alerte)

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Insights & Recommandations",
            "Visualisations",
            "Statistiques détaillées",
            "Export",
        ])

        with tab1:
            st.markdown(result["insights"])

        with tab2:
            charts = auto_visualisations(df)
            if charts:
                for fig in charts:
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Pas assez de colonnes numériques pour générer des visualisations automatiques.")

        with tab3:
            colonnes = stats.get("colonnes", [])
            if colonnes:
                df_cols = pd.DataFrame(colonnes)
                st.dataframe(df_cols, use_container_width=True, hide_index=True)

            stats_cles = stats.get("statistiques_cles", {})
            if stats_cles:
                st.markdown("**Statistiques numériques**")
                st.json(stats_cles)

        with tab4:
            col_pdf, col_csv = st.columns(2)

            with col_pdf:
                try:
                    pdf_bytes = generer_pdf(result, fichier.name, type_analyse)
                    st.download_button(
                        label="📄 Télécharger rapport PDF",
                        data=pdf_bytes,
                        file_name=f"analyse_{fichier.name.replace('.', '_')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"PDF indisponible : {e}")

            with col_csv:
                csv_str = df.to_csv(index=False, encoding="utf-8")
                st.download_button(
                    label="📊 Télécharger données CSV",
                    data=csv_str,
                    file_name=f"donnees_{fichier.name.replace('.', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )