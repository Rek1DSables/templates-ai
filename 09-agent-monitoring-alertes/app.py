# app.py
import json
import time
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from graph import build_graph
from config import (
    TYPES_METRIQUES, NIVEAUX_ALERTE, SEUILS_DEFAUT, SQL_SETUP
)

# Métriques de démo — système avec plusieurs violations
METRIQUES_DEMO = {
    "taux_erreur_api": 12.5,
    "temps_reponse_ms": 3200,
    "taux_conversion": 1.2,
    "churn_mensuel": 8.5,
    "cpu_usage": 92.0,
    "memoire_usage": 78.0,
    "ca_journalier": 450,
    "nb_tickets_ouverts": 35,
}

st.set_page_config(page_title="Agent Monitoring & Alertes", page_icon="📡", layout="centered")
st.title("📡 Agent Monitoring & Alertes")
st.caption("Détection violations → Analyse causale → Alertes graduées → Rapport → Notification Gmail")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Détection** — compare métriques vs seuils, calcule écarts et niveaux
2. **Agent Analyse Causale** — corrélations, cause racine, score de santé global
3. **Agent Génération Alertes** — alerte structurée par violation + sauvegarde Supabase
4. **Agent Rapport & Notification** — rapport synthétique + envoi Gmail optionnel
    """)

with st.expander("🗄️ Setup Supabase"):
    st.code(SQL_SETUP, language="sql")

st.divider()

col1, col2 = st.columns(2)
with col1:
    type_metriques = st.selectbox("Type de métriques", TYPES_METRIQUES)
with col2:
    contexte = st.text_input("Contexte business", placeholder="SaaS B2B, 500 clients actifs, phase de croissance")

mode_demo = st.toggle("Mode démo (métriques pré-remplies avec violations)", value=True)

st.subheader("Métriques à surveiller")

if mode_demo:
    metriques = METRIQUES_DEMO
    seuils = SEUILS_DEFAUT
    st.info("Mode démo — 8 métriques avec plusieurs violations intentionnelles")

    cols = st.columns(4)
    for i, (metrique, valeur) in enumerate(metriques.items()):
        seuil = SEUILS_DEFAUT.get(metrique, {}).get("seuil", 0)
        direction = SEUILS_DEFAUT.get(metrique, {}).get("direction", "above")
        unite = SEUILS_DEFAUT.get(metrique, {}).get("unite", "")
        violation = (direction == "above" and valeur > seuil) or (direction == "below" and valeur < seuil)
        icone = "🔴" if violation else "🟢"
        cols[i % 4].metric(
            label=metrique.replace("_", " ").title(),
            value=f"{valeur} {unite}",
            delta=f"Seuil : {seuil} {unite}",
            delta_color="inverse" if violation else "normal",
        )
else:
    st.caption("Configure les métriques et seuils manuellement")
    nb_metriques = st.number_input("Nombre de métriques", min_value=1, max_value=10, value=4)
    metriques = {}
    seuils = {}

    for i in range(nb_metriques):
        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 1])
        nom = c1.text_input(f"Métrique #{i+1}", placeholder="taux_erreur_api")
        valeur = c2.number_input(f"Valeur #{i+1}", value=0.0)
        seuil_val = c3.number_input(f"Seuil #{i+1}", value=0.0)
        unite = c4.text_input(f"Unité #{i+1}", placeholder="%")
        direction = c5.selectbox(f"Direction #{i+1}", ["above", "below"])
        if nom:
            metriques[nom] = valeur
            seuils[nom] = {"seuil": seuil_val, "unite": unite, "direction": direction}

st.divider()
st.subheader("Notification")
envoyer_email = st.toggle("Envoyer rapport par email si alertes critiques", value=False)
destinataire = ""
if envoyer_email:
    destinataire = st.text_input("Email destinataire", placeholder="ops@entreprise.com")

if st.button("Lancer le monitoring", use_container_width=True):
    if not metriques:
        st.error("Merci de configurer au moins une métrique.")
    else:
        with st.spinner("Analyse monitoring en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "metriques": metriques,
                    "seuils": seuils,
                    "type_metriques": type_metriques,
                    "contexte_business": contexte or "Système de production",
                    "destinataire_email": destinataire,
                    "envoyer_email": envoyer_email,
                    "mode_demo": mode_demo,
                    "violations": [],
                    "alertes_generees": [],
                    "analyse_causale": "",
                    "actions_recommandees": [],
                    "score_sante": 100,
                    "tendances": [],
                    "rapport_monitoring": "",
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        score = result["score_sante"]
        couleur_score = "🔴" if score < 40 else "🟠" if score < 60 else "🟡" if score < 80 else "🟢"
        nb_critiques = len([a for a in result["alertes_generees"] if a["niveau"] == "critique"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Score santé", f"{couleur_score} {score}/100")
        col2.metric("Violations", len(result["violations"]))
        col3.metric("Alertes critiques", nb_critiques)
        col4.metric("Actions requises", len(result["actions_recommandees"]))

        if nb_critiques > 0:
            st.error(f"🚨 {nb_critiques} alerte(s) CRITIQUE(S) — intervention immédiate requise")

        # Gauge score santé
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=score,
            title={"text": "Score de Santé Système"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "red" if score < 40 else "orange" if score < 60 else "yellow" if score < 80 else "green"},
                "steps": [
                    {"range": [0, 40], "color": "rgba(255,0,0,0.1)"},
                    {"range": [40, 60], "color": "rgba(255,165,0,0.1)"},
                    {"range": [60, 80], "color": "rgba(255,255,0,0.1)"},
                    {"range": [80, 100], "color": "rgba(0,255,0,0.1)"},
                ],
            }
        ))
        fig_gauge.update_layout(height=250)
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Alertes",
            "Analyse causale",
            "Rapport",
            "Audit Trail",
            "Export",
        ])

        with tab1:
            alertes = result["alertes_generees"]
            if not alertes:
                st.success("✅ Aucune violation — système dans les seuils normaux")
            else:
                for niveau in ["critique", "eleve", "moyen", "info"]:
                    alertes_niveau = [a for a in alertes if a["niveau"] == niveau]
                    if alertes_niveau:
                        icone = NIVEAUX_ALERTE.get(niveau, {}).get("icone", "🔵")
                        sla = NIVEAUX_ALERTE.get(niveau, {}).get("sla_minutes", 60)
                        st.subheader(f"{icone} {niveau.capitalize()} — SLA {sla} min ({len(alertes_niveau)})")
                        for a in alertes_niveau:
                            with st.expander(f"{a.get('metrique', '')} — {a.get('valeur_actuelle')} (seuil {a.get('seuil')})"):
                                st.markdown(f"**Message :** {a.get('message', '')}")
                                st.markdown(f"**Cause probable :** {a.get('cause_probable', '')}")
                                st.markdown(f"**Action immédiate :** {a.get('action_immediate', '')}")
                                st.markdown(f"**Responsable :** {a.get('responsable', '')} — {a.get('delai', '')}")
                                st.markdown(f"**Écart :** {a.get('ecart_pct', 0)}%")

        with tab2:
            st.markdown(result["analyse_causale"])
            if result["tendances"]:
                st.divider()
                st.markdown("**Tendances identifiées**")
                for t in result["tendances"]:
                    st.markdown(f"📈 {t}")
            if result["actions_recommandees"]:
                st.divider()
                st.markdown("**Actions recommandées**")
                for a in result["actions_recommandees"]:
                    st.markdown(f"→ {a}")

        with tab3:
            st.markdown(result["rapport_monitoring"])

        with tab4:
            for entry in result["audit_log"]:
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

        with tab5:
            col_a, col_b = st.columns(2)
            with col_a:
                if result["alertes_generees"]:
                    df_alertes = pd.DataFrame(result["alertes_generees"])
                    st.download_button(
                        label="📊 Alertes CSV",
                        data=df_alertes.to_csv(index=False, encoding="utf-8"),
                        file_name=f"alertes_{time.strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            with col_b:
                st.download_button(
                    label="📦 Rapport JSON complet",
                    data=json.dumps({
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "score_sante": result["score_sante"],
                        "violations": result["violations"],
                        "alertes": result["alertes_generees"],
                        "analyse_causale": result["analyse_causale"],
                        "actions": result["actions_recommandees"],
                        "audit_log": result["audit_log"],
                    }, ensure_ascii=False, indent=2),
                    file_name=f"monitoring_{time.strftime('%Y%m%d_%H%M')}.json",
                    mime="application/json",
                    use_container_width=True,
                )