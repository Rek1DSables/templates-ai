import streamlit as st
from graph import run_quote
from supabase import create_client
import config

st.set_page_config(
    page_title="Générateur de Devis",
    page_icon="📄",
    layout="wide",
)

st.title("📄 Générateur de Devis Automatique")
st.caption(f"LangGraph · FPDF2 · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2 = st.tabs(["➕ Nouveau devis", "📋 Historique"])

# ─── Tab 1 : Nouveau devis ────────────────────────────────────────────────────
with tab1:
    st.info(
        "Renseignez les informations client et le projet. Le pipeline va :\n"
        "1. Générer les lignes de devis adaptées au projet\n"
        "2. Calculer les montants HT/TVA/TTC\n"
        "3. Générer un PDF professionnel téléchargeable\n"
        "4. Enregistrer dans Supabase",
        icon="ℹ️",
    )

    with st.form("quote_form"):
        st.subheader("👤 Client")
        col1, col2, col3 = st.columns(3)
        with col1:
            client_name    = st.text_input("Nom complet *", placeholder="Marie Dupont")
        with col2:
            client_email   = st.text_input("Email *", placeholder="marie@dupont.fr")
        with col3:
            client_company = st.text_input("Entreprise", placeholder="Dupont & Co")

        st.subheader("📋 Projet")
        project_description = st.text_area(
            "Description du projet *",
            height=120,
            placeholder="Ex : Développement d'un pipeline IA de qualification de leads avec intégration CRM..."
        )
        budget_range = st.select_slider(
            "Budget indicatif",
            options=["< 1 000 €", "1 000 - 3 000 €", "3 000 - 5 000 €",
                     "5 000 - 10 000 €", "10 000 - 20 000 €", "> 20 000 €"],
            value="3 000 - 5 000 €"
        )

        submitted = st.form_submit_button("🚀 Générer le devis", use_container_width=True, type="primary")

    if submitted:
        if not client_name or not client_email or not project_description:
            st.error("⚠️ Les champs marqués * sont obligatoires.")
            st.stop()

        with st.status("⚙️ Génération en cours...", expanded=True) as pipeline_status:
            st.write("🤖 Analyse du projet et chiffrage...")
            st.write("📄 Génération du PDF...")
            st.write("💾 Enregistrement Supabase...")

            try:
                result = run_quote(
                    client_name         = client_name,
                    client_email        = client_email,
                    client_company      = client_company,
                    project_description = project_description,
                    budget_range        = budget_range,
                )

                if result["status"] == "error":
                    pipeline_status.update(label="❌ Erreur", state="error")
                    for err in result["errors"]:
                        st.error(err)

                elif result["status"] == "completed":
                    pipeline_status.update(label="✅ Devis généré !", state="complete", expanded=False)
                    st.success(f"✅ Devis **{result['quote_number']}** généré pour **{client_name}**")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("💰 Total HT",  f"{result['total_ht']:,.2f} €")
                    col2.metric("📊 TVA",        f"{result['total_tva']:,.2f} €")
                    col3.metric("💳 Total TTC",  f"{result['total_ttc']:,.2f} €")
                    col4.metric("📅 Validité",   result['validity_date'])

                    st.markdown("---")

                    st.subheader("📋 Lignes du devis")
                    for item in result["line_items"]:
                        col1, col2, col3, col4 = st.columns([5, 1, 2, 2])
                        col1.write(item["description"])
                        col2.write(f"{item['quantity']} {item.get('unit', '')}")
                        col3.write(f"{item['unit_price']:,.2f} €")
                        col4.write(f"**{item['total']:,.2f} €**")

                    st.markdown("---")

                    st.download_button(
                        label="⬇️ Télécharger le devis PDF",
                        data=result["pdf_bytes"],
                        file_name=f"devis_{result['quote_number']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )

            except Exception as e:
                pipeline_status.update(label="❌ Erreur inattendue", state="error")
                st.error(f"Erreur inattendue : {e}")

# ─── Tab 2 : Historique ───────────────────────────────────────────────────────
with tab2:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh_quotes"] = True

    if st.session_state.get("refresh_quotes", True):
        try:
            sb     = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            result = sb.table(config.SUPABASE_TABLE).select("*").order("created_at", desc=True).execute()
            quotes = result.data

            if quotes:
                total = sum(q.get("total_ttc", 0) for q in quotes)
                col1, col2 = st.columns(2)
                col1.metric("📄 Devis générés", len(quotes))
                col2.metric("💰 Volume total TTC", f"{total:,.2f} €")

                st.markdown("---")
                for q in quotes:
                    with st.expander(f"📄 {q['quote_number']} — {q['client_name']} — {q['total_ttc']:,.2f} €"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Client :** {q['client_name']}")
                            st.markdown(f"**Entreprise :** {q.get('client_company') or '—'}")
                            st.markdown(f"**Email :** {q['client_email']}")
                        with col2:
                            st.markdown(f"**HT :** {q['total_ht']:,.2f} €")
                            st.markdown(f"**TTC :** {q['total_ttc']:,.2f} €")
                            st.markdown(f"**Validité :** {q['validity_date']}")
                        st.markdown(f"**Projet :** {q['project_description'][:200]}...")
            else:
                st.info("Aucun devis généré pour l'instant.")

        except Exception as e:
            st.error(f"Erreur chargement : {e}")

        st.session_state["refresh_quotes"] = False

st.markdown("---")
st.caption("Template 23 — Générateur de devis · [GitHub](https://github.com/Rek1DSables/templates-ai)")