import streamlit as st
from graph import run_legal_watch
from supabase import create_client
import config

st.set_page_config(
    page_title="Veille Légale & Réglementaire",
    page_icon="⚖️",
    layout="centered",
)

st.title("⚖️ Agent de Veille Légale & Réglementaire")
st.caption(f"LangGraph · Serper · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2 = st.tabs(["🔍 Nouvelle veille", "📋 Historique"])

# ─── Tab 1 : Nouvelle veille ─────────────────────────────────────────────────
with tab1:
    st.info(
        "Lancez une veille réglementaire ciblée. Le pipeline va :\n"
        "1. Rechercher les actualités juridiques récentes\n"
        "2. Extraire les mises à jour pertinentes\n"
        "3. Analyser l'impact sur votre entreprise\n"
        "4. Générer un plan d'action de mise en conformité",
        icon="ℹ️",
    )

    with st.form("legal_watch_form"):
        st.subheader("🏢 Entreprise")
        col1, col2 = st.columns(2)
        with col1:
            company_name = st.text_input("Nom de l'entreprise *", placeholder="Dupont SAS")
        with col2:
            jurisdiction = st.selectbox("Juridiction *", config.JURISDICTIONS)

        company_context = st.text_area(
            "Description de l'activité *",
            height=80,
            placeholder="Ex : E-commerce B2C vendant des produits cosmétiques en France et en Europe..."
        )

        st.subheader("⚖️ Domaine juridique")
        legal_domain = st.selectbox("Domaine *", config.LEGAL_DOMAINS)

        submitted = st.form_submit_button("🚀 Lancer la veille", use_container_width=True, type="primary")

    if submitted:
        if not company_name or not company_context:
            st.error("⚠️ Tous les champs sont obligatoires.")
            st.stop()

        with st.status("⚙️ Veille en cours...", expanded=True) as pipeline_status:
            st.write("🔍 Recherche des actualités juridiques...")
            st.write("📋 Extraction des mises à jour...")
            st.write("⚖️ Analyse d'impact...")
            st.write("📝 Génération du plan d'action...")

            try:
                result = run_legal_watch(
                    company_name    = company_name,
                    legal_domain    = legal_domain,
                    jurisdiction    = jurisdiction,
                    company_context = company_context,
                )

                if result["status"] == "error":
                    pipeline_status.update(label="❌ Erreur", state="error")
                    for err in result["errors"]:
                        st.error(err)

                elif result["status"] == "completed":
                    pipeline_status.update(label="✅ Veille terminée !", state="complete", expanded=False)
                    st.success(f"✅ Veille **{legal_domain}** générée pour **{company_name}**")

                    st.markdown("---")

                    with st.expander("📋 Mises à jour réglementaires", expanded=True):
                        st.markdown(result["legal_updates"][0]["content"])

                    with st.expander("⚖️ Analyse d'impact", expanded=True):
                        st.markdown(result.get("impact_analysis", "—"))

                    with st.expander("📝 Plan d'action", expanded=True):
                        st.markdown(result.get("action_plan", "—"))

                    # Export
                    export = f"""VEILLE RÉGLEMENTAIRE — {company_name}
Domaine : {legal_domain} | Juridiction : {jurisdiction}
Date : {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}

MISES À JOUR :
{result['legal_updates'][0]['content']}

ANALYSE D'IMPACT :
{result.get('impact_analysis', '')}

PLAN D'ACTION :
{result.get('action_plan', '')}
"""
                    st.download_button(
                        label="⬇️ Télécharger le rapport",
                        data=export,
                        file_name=f"veille_{legal_domain[:20].replace(' ', '_')}.txt",
                        mime="text/plain",
                        use_container_width=True,
                    )

            except Exception as e:
                pipeline_status.update(label="❌ Erreur inattendue", state="error")
                st.error(f"Erreur inattendue : {e}")

# ─── Tab 2 : Historique ───────────────────────────────────────────────────────
with tab2:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh_legal"] = True

    if st.session_state.get("refresh_legal", True):
        try:
            sb     = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            result = sb.table(config.SUPABASE_TABLE).select("*").order("created_at", desc=True).execute()
            watches = result.data

            if watches:
                st.metric("📋 Veilles effectuées", len(watches))
                st.markdown("---")
                for w in watches:
                    with st.expander(f"⚖️ {w['company_name']} — {w['legal_domain']} — {w['created_at'][:10]}"):
                        st.markdown(f"**Juridiction :** {w['jurisdiction']}")
                        st.markdown(f"**Plan d'action :** {w.get('action_plan', '—')[:300]}...")
            else:
                st.info("Aucune veille effectuée pour l'instant.")

        except Exception as e:
            st.error(f"Erreur : {e}")

        st.session_state["refresh_legal"] = False

st.markdown("---")
st.caption("Template 28 — Veille légale & réglementaire · [GitHub](https://github.com/Rek1DSables/templates-ai)")