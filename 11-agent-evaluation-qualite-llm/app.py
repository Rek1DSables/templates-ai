# app.py
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from graph import build_graph
from config import (
    TYPES_TESTS, MODELES_DISPONIBLES, DIMENSIONS_EVALUATION,
    SEUILS_QUALITE, SEVERITES, CAS_TESTS_DEMO
)


st.set_page_config(page_title="Agent Évaluation Qualité LLM", page_icon="🔬", layout="centered")
st.title("🔬 Agent Évaluation Qualité LLM")
st.caption("Exécution tests → Évaluation multi-dimensions → Détection régressions → Rapport déployabilité")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Exécution** — exécute chaque cas de test sur le modèle évalué
2. **Agent Évaluation** — score chaque réponse sur 7 dimensions de qualité
3. **Agent Régression** — détecte hallucinations, toxicité, tests critiques échoués
4. **Agent Rapport** — rapport de déployabilité avec badge qualité
    """)

st.divider()

col1, col2 = st.columns(2)
with col1:
    modele = st.selectbox("Modèle à évaluer", MODELES_DISPONIBLES)
    if modele == "Modèle custom":
        modele = st.text_input("Model string custom", placeholder="mon-modele-v1")
with col2:
    environnement = st.selectbox("Environnement cible",
        ["Production (seuil 80)", "Staging (seuil 65)", "Dev (seuil 50)"])

system_prompt = st.text_area(
    "System prompt du modèle évalué (optionnel)",
    placeholder="Tu es un assistant customer support pour Acme Corp. Tu réponds uniquement en français...",
    height=80,
)

st.divider()
st.subheader("Cas de test")

source_tests = st.radio("Source", ["Cas de démo (5 tests)", "Saisie manuelle"], horizontal=True)

cas_tests = []

if source_tests == "Cas de démo (5 tests)":
    cas_tests = CAS_TESTS_DEMO
    df_demo = pd.DataFrame([{
        "ID": c["id"],
        "Type": c["type"],
        "Question": c["question"][:60] + "...",
        "Critique": "🔴" if c["critique"] else "🟢",
    } for c in cas_tests])
    st.dataframe(df_demo, use_container_width=True, hide_index=True)
else:
    nb_tests = st.number_input("Nombre de cas de test", min_value=1, max_value=20, value=2)
    for i in range(nb_tests):
        with st.expander(f"Cas de test #{i+1}"):
            c1, c2 = st.columns(2)
            test_id = c1.text_input(f"ID #{i+1}", value=f"TC{i+1:03d}")
            type_test = c2.selectbox(f"Type #{i+1}", TYPES_TESTS)
            question = st.text_area(f"Question #{i+1}", height=80)
            reponse_attendue = st.text_input(f"Réponse attendue #{i+1}")
            contexte = st.text_input(f"Contexte #{i+1} (optionnel)")
            critique = st.checkbox(f"Test critique #{i+1}", value=False)
            cas_tests.append({
                "id": test_id,
                "type": type_test,
                "question": question,
                "reponse_attendue": reponse_attendue,
                "contexte": contexte,
                "critique": critique,
            })

if st.button("Lancer l'évaluation", use_container_width=True):
    if not cas_tests or not modele:
        st.error("Merci de configurer le modèle et les cas de test.")
    else:
        with st.spinner(f"Évaluation de {modele} en cours — {len(cas_tests)} tests..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "modele_evalue": modele,
                    "system_prompt": system_prompt or "Tu es un assistant utile et précis.",
                    "cas_tests": cas_tests,
                    "resultats_bruts": [],
                    "scores_par_dimension": {},
                    "regressions": [],
                    "rapport_qualite": "",
                    "score_global": 0,
                    "recommandations": [],
                    "badge_qualite": "",
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_global"]
        badge = result["badge_qualite"]
        nb_fails = len([r for r in result["resultats_bruts"] if not r.get("evaluation", {}).get("passed")])
        nb_regressions = len([r for r in result["regressions"] if r["severite"] == "bloquant"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score global", f"{score}/100")
        col2.metric("Badge", badge.split(" ", 1)[1] if " " in badge else badge)
        col3.metric("Tests échoués", nb_fails)
        col4.metric("Régressions bloquantes", nb_regressions)

        st.info(f"**Verdict déployabilité :** {badge}")

        if nb_regressions > 0:
            st.error(f"🚨 {nb_regressions} régression(s) bloquante(s) — déploiement non recommandé")

        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Résultats tests",
            "Scores dimensions",
            "Régressions",
            "Rapport",
            "Export",
        ])

        with tab1:
            rows = []
            for r in result["resultats_bruts"]:
                eval_data = r.get("evaluation", {})
                rows.append({
                    "ID": r["id"],
                    "Type": r["type"],
                    "Score": eval_data.get("score_global", 0),
                    "Statut": "✅ PASS" if eval_data.get("passed") else "❌ FAIL",
                    "Critique": "🔴" if r.get("critique") else "🟢",
                    "Latence": f"{r.get('latence_ms', 0)}ms",
                    "Problèmes": ", ".join(eval_data.get("problemes", []))[:50],
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            for r in result["resultats_bruts"]:
                eval_data = r.get("evaluation", {})
                icone = "✅" if eval_data.get("passed") else "❌"
                with st.expander(f"{icone} {r['id']} — {r['type']} — Score {eval_data.get('score_global', 0)}/100"):
                    st.markdown(f"**Question :** {r['question']}")
                    st.markdown(f"**Réponse attendue :** {r['reponse_attendue']}")
                    st.markdown(f"**Réponse obtenue :** {r.get('reponse_obtenue', '')[:300]}")
                    st.markdown(f"**Commentaire :** {eval_data.get('commentaire', '')}")
                    if eval_data.get("problemes"):
                        for p in eval_data["problemes"]:
                            st.warning(p)

        with tab2:
            scores = result["scores_par_dimension"]
            if scores:
                fig_radar = go.Figure()
                dimensions = list(scores.keys())
                valeurs = list(scores.values())
                valeurs.append(valeurs[0])
                dimensions.append(dimensions[0])

                fig_radar.add_trace(go.Scatterpolar(
                    r=valeurs,
                    theta=dimensions,
                    fill="toself",
                    name=modele,
                    line_color="blue",
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    title=f"Scores par dimension — {modele}",
                    height=400,
                )
                st.plotly_chart(fig_radar, use_container_width=True)

                df_scores = pd.DataFrame([
                    {"Dimension": dim, "Score": score, "Seuil prod": 80,
                     "Statut": "✅" if score >= 80 else "⚠️" if score >= 60 else "❌"}
                    for dim, score in scores.items()
                ])
                st.dataframe(df_scores, use_container_width=True, hide_index=True)

        with tab3:
            regressions = result["regressions"]
            if not regressions:
                st.success("✅ Aucune régression détectée")
            else:
                for sev in ["bloquant", "majeur", "mineur", "info"]:
                    regs_sev = [r for r in regressions if r["severite"] == sev]
                    if regs_sev:
                        icone = SEVERITES.get(sev, "🟡")
                        st.subheader(f"{icone} {sev.capitalize()} ({len(regs_sev)})")
                        for reg in regs_sev:
                            with st.expander(f"{reg['type']} — {reg['test_id']}"):
                                st.markdown(f"**Description :** {reg['description']}")
                                st.markdown(f"**Impact :** {reg['impact']}")

        with tab4:
            st.markdown(result["rapport_qualite"])
            if result["recommandations"]:
                st.divider()
                st.markdown("**Recommandations**")
                for rec in result["recommandations"]:
                    st.markdown(f"→ {rec}")

        with tab5:
            export_data = {
                "modele": modele,
                "score_global": result["score_global"],
                "badge": result["badge_qualite"],
                "scores_par_dimension": result["scores_par_dimension"],
                "resultats": result["resultats_bruts"],
                "regressions": result["regressions"],
                "audit_log": result["audit_log"],
            }
            st.download_button(
                label="📦 Rapport complet JSON",
                data=json.dumps(export_data, ensure_ascii=False, indent=2),
                file_name=f"eval_{modele.replace('/', '_')}.json",
                mime="application/json",
                use_container_width=True,
            )

            if result["resultats_bruts"]:
                rows_export = []
                for r in result["resultats_bruts"]:
                    eval_data = r.get("evaluation", {})
                    row = {
                        "id": r["id"],
                        "type": r["type"],
                        "question": r["question"],
                        "reponse_attendue": r["reponse_attendue"],
                        "reponse_obtenue": r.get("reponse_obtenue", ""),
                        "score_global": eval_data.get("score_global", 0),
                        "passed": eval_data.get("passed", False),
                        "latence_ms": r.get("latence_ms", 0),
                    }
                    row.update({f"score_{dim}": eval_data.get("scores", {}).get(dim, 0)
                                for dim in ["fidelite", "completude", "precision", "hallucination"]})
                    rows_export.append(row)

                df_export = pd.DataFrame(rows_export)
                st.download_button(
                    label="📊 Résultats CSV",
                    data=df_export.to_csv(index=False, encoding="utf-8"),
                    file_name=f"eval_{modele.replace('/', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )