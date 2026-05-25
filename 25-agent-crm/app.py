import streamlit as st
from graph import run_action
from supabase import create_client
import config

st.set_page_config(
    page_title="Agent CRM",
    page_icon="🤝",
    layout="wide",
)

st.title("🤝 Agent CRM Intelligent")
st.caption(f"LangGraph · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Pipeline", "➕ Nouveau contact", "📝 Interactions", "🔍 Fiche contact"])

# ─── Tab 1 : Pipeline ─────────────────────────────────────────────────────────
with tab1:
    if st.button("🔄 Actualiser le pipeline", use_container_width=True):
        with st.spinner("Chargement..."):
            result = run_action("get_pipeline")

            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                stats = result.get("pipeline_stats", {})
                opps  = result.get("opportunities", [])

                # Métriques globales
                total_value = sum(v["value"] for v in stats.values())
                total_count = sum(v["count"] for v in stats.values())
                won         = stats.get("Gagné", {}).get("value", 0)

                col1, col2, col3 = st.columns(3)
                col1.metric("💰 Pipeline total",  f"{total_value:,.0f} €")
                col2.metric("📋 Opportunités",    total_count)
                col3.metric("✅ CA gagné",        f"{won:,.0f} €")

                st.markdown("---")

                # Kanban par étape
                st.subheader("📊 Pipeline par étape")
                cols = st.columns(len(config.PIPELINE_STAGES))
                for i, stage in enumerate(config.PIPELINE_STAGES):
                    with cols[i]:
                        s = stats.get(stage, {"count": 0, "value": 0})
                        st.markdown(f"**{stage}**")
                        st.metric("Nb", s["count"])
                        st.metric("Valeur", f"{s['value']:,.0f}€")

                st.markdown("---")

                with st.expander("🤖 Analyse IA du pipeline", expanded=True):
                    st.markdown(result.get("summary", "—"))

                st.markdown("---")

                st.subheader("📋 Opportunités")
                for o in opps:
                    stage_icon = {
                        "Prospect": "🔵", "Qualifié": "🟡",
                        "Proposition envoyée": "🟠", "Négociation": "🔴",
                        "Gagné": "✅", "Perdu": "❌"
                    }.get(o["stage"], "🔵")
                    st.markdown(
                        f"{stage_icon} **{o['contact_name']}** — {o['company']} — "
                        f"{o['stage']} — {o.get('deal_value', 0):,.0f}€ | `{o['contact_id'][:8]}...`"
                    )

# ─── Tab 2 : Nouveau contact ──────────────────────────────────────────────────
with tab2:
    with st.form("contact_form"):
        st.subheader("👤 Informations contact")
        col1, col2 = st.columns(2)
        with col1:
            name    = st.text_input("Nom complet *", placeholder="Marie Dupont")
            email   = st.text_input("Email *", placeholder="marie@dupont.fr")
        with col2:
            company = st.text_input("Entreprise *", placeholder="Dupont & Co")
            phone   = st.text_input("Téléphone", placeholder="+33 6 12 34 56 78")

        deal_value = st.number_input("Valeur estimée du deal (€)", min_value=0.0, step=100.0)

        submitted = st.form_submit_button("➕ Ajouter le contact", use_container_width=True, type="primary")

    if submitted:
        if not name or not email or not company:
            st.error("⚠️ Nom, email et entreprise sont obligatoires.")
        else:
            result = run_action(
                "add_contact",
                name       = name,
                email      = email,
                company    = company,
                phone      = phone,
                deal_value = deal_value,
            )
            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                st.success(f"✅ Contact ajouté ! ID : `{result.get('contact_id', '—')}`")

# ─── Tab 3 : Interactions ─────────────────────────────────────────────────────
with tab3:
    st.subheader("📝 Enregistrer une interaction")

    with st.form("interaction_form"):
        contact_id       = st.text_input("ID contact *", placeholder="Copiez l'ID depuis le pipeline")
        interaction_type = st.selectbox("Type d'interaction *", config.INTERACTION_TYPES)
        note             = st.text_area("Note *", placeholder="Résumé de l'échange...", height=100)
        submitted        = st.form_submit_button("📝 Enregistrer", use_container_width=True, type="primary")

    if submitted:
        if not contact_id or not note:
            st.error("⚠️ ID contact et note sont obligatoires.")
        else:
            result = run_action(
                "add_interaction",
                contact_id       = contact_id,
                interaction_type = interaction_type,
                interaction_note = note,
            )
            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                st.success("✅ Interaction enregistrée !")

    st.markdown("---")
    st.subheader("📈 Mettre à jour l'étape")

    with st.form("stage_form"):
        contact_id_stage = st.text_input("ID contact *", placeholder="Copiez l'ID depuis le pipeline", key="stage_contact")
        new_stage        = st.selectbox("Nouvelle étape *", config.PIPELINE_STAGES)
        submitted_stage  = st.form_submit_button("📈 Mettre à jour", use_container_width=True, type="primary")

    if submitted_stage:
        if not contact_id_stage:
            st.error("⚠️ L'ID contact est obligatoire.")
        else:
            result = run_action("update_stage", contact_id=contact_id_stage, new_stage=new_stage)
            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                st.success(f"✅ Étape mise à jour : **{new_stage}**")

# ─── Tab 4 : Fiche contact ────────────────────────────────────────────────────
with tab4:
    contact_id_search = st.text_input("ID contact", placeholder="Entrez l'ID du contact")
    if st.button("🔍 Générer la fiche", use_container_width=True, type="primary"):
        if not contact_id_search:
            st.error("⚠️ L'ID est obligatoire.")
        else:
            with st.spinner("Génération de la fiche..."):
                result = run_action("get_contact_summary", contact_id=contact_id_search)
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    contact = result["contacts"][0] if result.get("contacts") else {}
                    opps    = result.get("opportunities", [])

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Nom :** {contact.get('name', '—')}")
                        st.markdown(f"**Entreprise :** {contact.get('company', '—')}")
                        st.markdown(f"**Email :** {contact.get('email', '—')}")
                    with col2:
                        st.markdown(f"**Étape :** {opps[0]['stage'] if opps else '—'}")
                        st.markdown(f"**Deal :** {opps[0].get('deal_value', 0):,.0f}€" if opps else "—")
                        st.markdown(f"**Interactions :** {len(result.get('interactions', []))}")

                    st.markdown("---")
                    with st.expander("🤖 Analyse IA", expanded=True):
                        st.markdown(result.get("summary", "—"))

st.markdown("---")
st.caption("Template 25 — Agent CRM · [GitHub](https://github.com/Rek1DSables/templates-ai)")