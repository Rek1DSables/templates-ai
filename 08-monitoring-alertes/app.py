import streamlit as st
from graph import run_monitoring
from supabase import create_client
import config

st.set_page_config(
    page_title="Monitoring & Alertes",
    page_icon="📡",
    layout="wide",
)

st.title("📡 Agent Monitoring & Alertes Intelligentes")
st.caption(f"LangGraph · Gmail · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2 = st.tabs(["📊 Monitoring", "📋 Historique alertes"])

# ─── Tab 1 : Monitoring ───────────────────────────────────────────────────────
with tab1:
    st.info(
        "Saisissez les métriques à surveiller. Le pipeline va :\n"
        "1. Détecter les anomalies selon les seuils définis\n"
        "2. Analyser la cause probable via IA\n"
        "3. Enregistrer dans Supabase\n"
        "4. Envoyer un email si alerte critique",
        icon="ℹ️",
    )

    with st.form("monitoring_form"):
        st.subheader("🖥️ Contexte système")
        context = st.text_input(
            "Nom du système / application *",
            placeholder="API Production — Serveur EU-West-1",
        )

        st.subheader("📊 Métriques actuelles")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Valeurs mesurées**")
            cpu_usage     = st.number_input("CPU Usage (%)",      min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            memory_usage  = st.number_input("Memory Usage (%)",   min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            disk_usage    = st.number_input("Disk Usage (%)",     min_value=0.0, max_value=100.0, value=0.0, step=0.1)
            response_time = st.number_input("Response Time (ms)", min_value=0.0, value=0.0, step=10.0)
            error_rate    = st.number_input("Error Rate (%)",     min_value=0.0, max_value=100.0, value=0.0, step=0.1)

        with col2:
            st.markdown("**Seuils d'alerte**")
            t_cpu     = st.number_input("Seuil CPU (%)",          min_value=0.0, max_value=100.0, value=config.DEFAULT_THRESHOLDS["cpu_usage"],      step=1.0)
            t_memory  = st.number_input("Seuil Memory (%)",       min_value=0.0, max_value=100.0, value=config.DEFAULT_THRESHOLDS["memory_usage"],   step=1.0)
            t_disk    = st.number_input("Seuil Disk (%)",         min_value=0.0, max_value=100.0, value=config.DEFAULT_THRESHOLDS["disk_usage"],     step=1.0)
            t_response = st.number_input("Seuil Response (ms)",   min_value=0.0,                  value=config.DEFAULT_THRESHOLDS["response_time"],  step=100.0)
            t_error   = st.number_input("Seuil Error Rate (%)",   min_value=0.0, max_value=100.0, value=config.DEFAULT_THRESHOLDS["error_rate"],     step=0.5)

        submitted = st.form_submit_button("🚀 Analyser les métriques", use_container_width=True, type="primary")

    if submitted:
        if not context:
            st.error("⚠️ Le nom du système est obligatoire.")
            st.stop()

        metrics = {
            "cpu_usage":     cpu_usage,
            "memory_usage":  memory_usage,
            "disk_usage":    disk_usage,
            "response_time": response_time,
            "error_rate":    error_rate,
        }

        thresholds = {
            "cpu_usage":     t_cpu,
            "memory_usage":  t_memory,
            "disk_usage":    t_disk,
            "response_time": t_response,
            "error_rate":    t_error,
        }

        with st.status("⚙️ Analyse en cours...", expanded=True) as pipeline_status:
            st.write("🔍 Détection des anomalies...")
            st.write("🤖 Analyse IA en cours...")

            try:
                result = run_monitoring(
                    metrics    = metrics,
                    thresholds = thresholds,
                    context    = context,
                )

                final_status = result.get("status", "error")

                if final_status == "error":
                    pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                    for err in result.get("errors", ["Erreur inconnue."]):
                        st.error(err)

                elif final_status == "completed":
                    anomalies = result.get("anomalies", [])
                    has_alert = any(a["ratio"] >= 1.0 for a in anomalies)

                    if has_alert:
                        pipeline_status.update(label="🚨 Anomalies détectées !", state="error", expanded=False)
                    else:
                        pipeline_status.update(label="✅ Tous les systèmes sont OK", state="complete", expanded=False)

                    # Métriques
                    critical = len([a for a in anomalies if "CRITIQUE" in a["level"]])
                    warning  = len([a for a in anomalies if "AVERTISSEMENT" in a["level"]])
                    ok       = len([a for a in anomalies if "OK" in a["level"]])

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("🔴 Critiques",      critical)
                    col2.metric("🟡 Avertissements", warning)
                    col3.metric("🟢 OK",             ok)
                    col4.metric("📧 Email envoyé",   "✓" if result.get("alert_sent") else "—")

                    st.markdown("---")

                    # Tableau métriques
                    st.subheader("📊 État des métriques")
                    for a in anomalies:
                        col1, col2, col3, col4 = st.columns([3, 2, 2, 2])
                        col1.write(f"**{a['metric']}**")
                        col2.write(f"Valeur : `{a['value']}`")
                        col3.write(f"Seuil : `{a['threshold']}`")
                        col4.write(a["level"])

                    # Analyse IA
                    st.markdown("---")
                    with st.expander("🤖 Analyse IA & Recommandations", expanded=True):
                        st.markdown(result.get("analysis", "—"))

                    # Erreurs non bloquantes
                    if result.get("errors"):
                        with st.expander("⚠️ Avertissements non bloquants"):
                            for err in result["errors"]:
                                st.warning(err)

            except Exception as e:
                pipeline_status.update(label="❌ Erreur inattendue", state="error")
                st.error(f"Erreur inattendue : {e}")

# ─── Tab 2 : Historique ───────────────────────────────────────────────────────
with tab2:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh_alerts"] = True

    if st.session_state.get("refresh_alerts", True):
        try:
            sb      = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            result  = sb.table(config.SUPABASE_TABLE).select("*").order("created_at", desc=True).limit(50).execute()
            alerts  = result.data

            if alerts:
                total    = len(alerts)
                critical = len([a for a in alerts if a.get("has_alert")])

                col1, col2 = st.columns(2)
                col1.metric("📋 Total analyses", total)
                col2.metric("🚨 Avec alertes",   critical)

                st.markdown("---")

                for alert in alerts:
                    icon = "🚨" if alert.get("has_alert") else "✅"
                    with st.expander(f"{icon} {alert.get('context', '—')} — {alert.get('created_at', '—')[:16]}"):
                        st.markdown(f"**Analyse :** {alert.get('analysis', '—')}")
            else:
                st.info("Aucune analyse enregistrée pour l'instant.")

        except Exception as e:
            st.error(f"Erreur chargement historique : {e}")

        st.session_state["refresh_alerts"] = False

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 18 — Monitoring & Alertes · [GitHub](https://github.com/Rek1DSables/templates-ai)")