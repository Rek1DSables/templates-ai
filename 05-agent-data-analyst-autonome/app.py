# app.py
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from graph import build_graph, init_demo_db, get_schema_info
from config import EXEMPLES_QUESTIONS


# Init DB demo
init_demo_db()

st.set_page_config(page_title="Agent Data Analyst Autonome", page_icon="🧠", layout="centered")
st.title("🧠 Agent Data Analyst Autonome")
st.caption("Posez une question en langage naturel → SQL généré → Exécution → Insights → Commentaire exécutif")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Text-to-SQL** — traduit la question en SQL valide avec auto-correction
2. **Agent Exécution & Validation** — exécute le SQL, retente si erreur
3. **Agent Analyse Insights** — analyse les résultats, détecte tendances et anomalies
4. **Agent Commentaire Exécutif** — synthèse en 3 phrases pour le management
    """)

with st.expander("🗄️ Schéma de la base de données"):
    schema = get_schema_info()
    st.code(schema, language="sql")

st.divider()

st.subheader("Posez votre question")

col1, col2 = st.columns([3, 1])
with col1:
    question = st.text_input(
        "Question en langage naturel",
        placeholder="Quel est le chiffre d'affaires total par région ?"
    )
with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    exemple = st.selectbox("Exemples", [""] + EXEMPLES_QUESTIONS, label_visibility="collapsed")

if exemple and not question:
    question = exemple

if question:
    st.info(f"**Question :** {question}")

if st.button("Analyser", use_container_width=True, disabled=not question):
    with st.spinner("Pipeline data analyst en cours..."):
        try:
            schema_info = get_schema_info()
            graph = build_graph()
            result = graph.invoke({
                "question": question,
                "schema_info": schema_info,
                "sql_genere": "",
                "sql_valide": False,
                "resultats_bruts": [],
                "nb_resultats": 0,
                "analyse": "",
                "visualisation_config": {},
                "commentaire_executif": "",
                "audit_log": [],
                "erreur": "",
            })
        except Exception as e:
            st.error(f"Erreur : {e}")
            st.stop()

    if result["erreur"]:
        st.error(result["erreur"])
        st.stop()

    # Métriques
    col1, col2, col3 = st.columns(3)
    col1.metric("Résultats", result["nb_resultats"])
    col2.metric("Type viz", result["visualisation_config"].get("type", "table").upper())
    col3.metric("Étapes", len(result["audit_log"]))

    # Commentaire exécutif
    if result["commentaire_executif"]:
        st.success(f"💡 **Synthèse executive :** {result['commentaire_executif']}")

    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs([
        "Visualisation",
        "Analyse détaillée",
        "SQL & Données brutes",
        "Audit Trail",
    ])

    with tab1:
        df = pd.DataFrame(result["resultats_bruts"])
        if df.empty:
            st.warning("Aucun résultat.")
        else:
            viz_config = result["visualisation_config"]
            viz_type = viz_config.get("type", "table")
            axe_x = viz_config.get("axe_x", df.columns[0] if len(df.columns) > 0 else "")
            axe_y = viz_config.get("axe_y", df.columns[1] if len(df.columns) > 1 else "")

            # Vérifier que les colonnes existent
            if axe_x not in df.columns:
                axe_x = df.columns[0]
            if axe_y not in df.columns and len(df.columns) > 1:
                axe_y = df.columns[1]

            try:
                if viz_type == "bar" and axe_x and axe_y and axe_y in df.columns:
                    fig = px.bar(df, x=axe_x, y=axe_y, title=question,
                        color=axe_y, color_continuous_scale="Blues")
                    st.plotly_chart(fig, use_container_width=True)

                elif viz_type == "line" and axe_x and axe_y and axe_y in df.columns:
                    fig = px.line(df, x=axe_x, y=axe_y, title=question, markers=True)
                    st.plotly_chart(fig, use_container_width=True)

                elif viz_type == "pie" and axe_x and axe_y and axe_y in df.columns:
                    fig = px.pie(df, names=axe_x, values=axe_y, title=question)
                    st.plotly_chart(fig, use_container_width=True)

                elif viz_type == "scatter" and axe_x and axe_y and axe_y in df.columns:
                    fig = px.scatter(df, x=axe_x, y=axe_y, title=question)
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.dataframe(df, use_container_width=True, hide_index=True)

            except Exception:
                st.dataframe(df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown(result["analyse"])

    with tab3:
        st.markdown("**SQL généré**")
        st.code(result["sql_genere"], language="sql")
        st.caption(f"Explication : {result['visualisation_config'].get('explication', '')}")

        st.divider()
        st.markdown("**Données brutes**")
        df_brut = pd.DataFrame(result["resultats_bruts"])
        if not df_brut.empty:
            st.dataframe(df_brut, use_container_width=True, hide_index=True)
            st.download_button(
                label="📊 Télécharger CSV",
                data=df_brut.to_csv(index=False, encoding="utf-8"),
                file_name="resultats.csv",
                mime="text/csv",
                use_container_width=True,
            )

    with tab4:
        for entry in result["audit_log"]:
            st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

        st.download_button(
            label="📦 Télécharger Audit Trail JSON",
            data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
            file_name="audit_data_analyst.json",
            mime="application/json",
            use_container_width=True,
        )