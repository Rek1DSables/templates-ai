# app.py
import json
import streamlit as st
import pandas as pd
from graph import build_graph
from config import (
    TYPES_INTEGRATION, SYSTEMES_CIBLES, STRATEGIES_RETRY,
    PAYLOADS_DEMO, SQL_SETUP
)


st.set_page_config(page_title="Agent Intégration SI & Webhook", page_icon="🔌", layout="centered")
st.title("🔌 Agent Intégration SI & Webhook")
st.caption("Réception → Validation → Transformation → Envoi multi-destinations → Retry → Dead Letter")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Réception & Validation** — déduplique (event_id idempotent), valide le payload IA
2. **Agent Transformation & Mapping** — adapte le format pour chaque destination
3. **Agent Envoi & Retry** — envoie avec retry configurable + dead letter automatique
4. **Agent Rapport** — métriques d'intégration + recommandations

**Patterns implémentés :**
- Idempotency (SHA-256 event_id)
- Retry avec backoff exponentiel / linéaire / fixe
- Dead Letter Queue (Supabase)
- Routeur conditionnel (payload invalide → dead letter direct)
    """)

with st.expander("🗄️ Setup Supabase"):
    st.code(SQL_SETUP, language="sql")

st.divider()

mode_demo = st.toggle("Mode démo (payloads fictifs, envois simulés)", value=True)

st.subheader("Configuration de l'intégration")

col1, col2 = st.columns(2)
with col1:
    type_integration = st.selectbox("Type d'intégration", TYPES_INTEGRATION)
    systeme_source = st.text_input("Système source", placeholder="Stripe / GitHub / HubSpot")
with col2:
    strategie_retry = st.selectbox("Stratégie de retry",
        list(STRATEGIES_RETRY.keys()),
        format_func=lambda x: f"{x} ({STRATEGIES_RETRY[x]['max_attempts']} tentatives max)")
    systemes_destinations = st.multiselect(
        "Systèmes destinations",
        SYSTEMES_CIBLES,
        default=["CRM (HubSpot / Salesforce)", "Base de données (PostgreSQL / Supabase)"],
    )

st.divider()
st.subheader("Payload entrant")

if mode_demo:
    payload_choisi = st.selectbox("Payload de démo", list(PAYLOADS_DEMO.keys()))
    payload_entrant = PAYLOADS_DEMO[payload_choisi]
    systeme_source = payload_choisi.split(" — ")[0] if " — " in payload_choisi else systeme_source
    st.json(payload_entrant)
else:
    payload_str = st.text_area(
        "Payload JSON",
        height=200,
        placeholder='{"event": "payment.received", "amount": 4900, "customer_id": "cus_123"}',
    )
    try:
        payload_entrant = json.loads(payload_str) if payload_str else {}
    except Exception:
        st.error("JSON invalide")
        payload_entrant = {}

if st.button("Traiter l'événement", use_container_width=True):
    if not payload_entrant:
        st.error("Merci de fournir un payload.")
    elif not systemes_destinations:
        st.error("Merci de sélectionner au moins une destination.")
    else:
        with st.spinner("Pipeline SI en cours — 4 agents..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "type_integration": type_integration,
                    "payload_entrant": payload_entrant,
                    "systeme_source": systeme_source,
                    "systemes_destinations": systemes_destinations,
                    "strategie_retry": strategie_retry,
                    "mode_demo": mode_demo,
                    "event_id": "",
                    "payload_valide": True,
                    "erreurs_validation": [],
                    "payload_transforme": {},
                    "mapping_effectue": {},
                    "tentatives": {},
                    "resultats_envoi": [],
                    "dead_letter": [],
                    "rapport_integration": "",
                    "statut_global": "",
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        statut = result["statut_global"]
        icone_statut = "✅" if statut == "success" else "⚠️" if statut == "partial" else "❌"
        nb_succes = len([r for r in result["resultats_envoi"] if r["succes"]])
        nb_total = len(result["resultats_envoi"])
        nb_dead = len(result["dead_letter"])

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Statut", f"{icone_statut} {statut.upper()}")
        col2.metric("Event ID", result["event_id"][:8] + "...")
        col3.metric("Succès", f"{nb_succes}/{nb_total}")
        col4.metric("Dead Letters", nb_dead)

        if nb_dead > 0:
            st.error(f"🚨 {nb_dead} événement(s) en Dead Letter Queue — intervention requise")

        st.divider()

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Résultats envoi",
            "Transformation",
            "Rapport",
            "Audit Trail",
            "Export",
        ])

        with tab1:
            for r in result["resultats_envoi"]:
                icone = "✅" if r["succes"] else "❌"
                with st.expander(f"{icone} {r['destination']} — {r['tentatives']} tentative(s) — HTTP {r['code_http']}"):
                    st.markdown(f"**Event ID :** `{r['event_id']}`")
                    st.markdown(f"**Message :** {r['message']}")
                    st.markdown(f"**Succès :** {'Oui' if r['succes'] else 'Non'}")

            if result["dead_letter"]:
                st.divider()
                st.subheader("💀 Dead Letter Queue")
                for dl in result["dead_letter"]:
                    with st.expander(f"❌ {dl['destination']} — {dl['erreur'][:60]}"):
                        st.markdown(f"**Erreur :** {dl['erreur']}")
                        st.markdown(f"**Tentatives :** {dl['tentatives']}")
                        st.json(dl["payload"])

        with tab2:
            mapping = result["mapping_effectue"]
            if mapping.get("mappings"):
                st.markdown("**Mappings effectués**")
                df_mapping = pd.DataFrame(mapping["mappings"])
                st.dataframe(df_mapping, use_container_width=True, hide_index=True)

            if mapping.get("enrichissements"):
                st.markdown("**Enrichissements**")
                for e in mapping["enrichissements"]:
                    st.markdown(f"✨ {e}")

            if mapping.get("payload_par_destination"):
                st.markdown("**Payload par destination**")
                for dest, payload in mapping["payload_par_destination"].items():
                    with st.expander(f"📦 {dest}"):
                        st.json(payload)

        with tab3:
            st.markdown(result["rapport_integration"])

        with tab4:
            for entry in result["audit_log"]:
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')} {('| ' + entry.get('detail', '')) if entry.get('detail') else ''}")

            st.download_button(
                label="📦 Audit Trail JSON",
                data=json.dumps(result["audit_log"], ensure_ascii=False, indent=2),
                file_name=f"audit_si_{result['event_id']}.json",
                mime="application/json",
                use_container_width=True,
            )

        with tab5:
            export = {
                "event_id": result["event_id"],
                "statut": result["statut_global"],
                "payload_original": payload_entrant,
                "payload_transforme": result["payload_transforme"],
                "resultats_envoi": result["resultats_envoi"],
                "dead_letter": result["dead_letter"],
                "audit_log": result["audit_log"],
            }
            st.download_button(
                label="📦 Rapport complet JSON",
                data=json.dumps(export, ensure_ascii=False, indent=2),
                file_name=f"integration_{result['event_id']}.json",
                mime="application/json",
                use_container_width=True,
            )