import streamlit as st
from graph import run_invoice
from supabase import create_client
import config

st.set_page_config(
    page_title="Automatisation Comptable",
    page_icon="🧾",
    layout="wide",
)

st.title("🧾 Pipeline Automatisation Comptable")
st.caption(f"LangGraph · PyMuPDF · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2 = st.tabs(["📤 Traiter une facture", "📊 Historique"])

# ─── Tab 1 : Traiter une facture ─────────────────────────────────────────────
with tab1:
    st.info(
        "Uploadez une facture PDF. Le pipeline va :\n"
        "1. Extraire le texte du PDF\n"
        "2. Identifier automatiquement les données clés (fournisseur, montants, TVA...)\n"
        "3. Valider la cohérence des montants\n"
        "4. Enregistrer dans Supabase",
        icon="ℹ️",
    )

    uploaded_file = st.file_uploader("Facture PDF *", type=["pdf"])

    if st.button("🚀 Traiter la facture", use_container_width=True, type="primary", disabled=not uploaded_file):
        with st.status("⚙️ Traitement en cours...", expanded=True) as pipeline_status:
            st.write("📄 Extraction du texte...")
            st.write("🤖 Analyse IA de la facture...")
            st.write("✅ Validation des montants...")
            st.write("💾 Enregistrement Supabase...")

            try:
                result = run_invoice(
                    file_bytes = uploaded_file.read(),
                    file_name  = uploaded_file.name,
                )

                final_status = result.get("status", "error")

                if final_status == "error":
                    pipeline_status.update(label="❌ Erreur — pipeline interrompu", state="error")
                    for err in result.get("errors", ["Erreur inconnue."]):
                        st.error(err)

                elif final_status == "completed":
                    pipeline_status.update(label="✅ Facture traitée !", state="complete", expanded=False)

                    data = result.get("validated_data", {})

                    st.success(f"✅ Facture **{data.get('invoice_number', '—')}** enregistrée.")

                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("💰 Montant HT",  f"{data.get('amount_ht', 0):,.2f} €")
                    col2.metric("📊 TVA",          f"{data.get('tva_amount', 0):,.2f} €")
                    col3.metric("💳 Montant TTC",  f"{data.get('amount_ttc', 0):,.2f} €")
                    col4.metric("🏷️ Catégorie",    data.get("category", "—"))

                    st.markdown("---")

                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Fournisseur :** {data.get('supplier_name', '—')}")
                        st.markdown(f"**SIRET :** {data.get('supplier_siret') or 'Non renseigné'}")
                        st.markdown(f"**N° Facture :** {data.get('invoice_number', '—')}")
                    with col2:
                        st.markdown(f"**Date facture :** {data.get('invoice_date', '—')}")
                        st.markdown(f"**Échéance :** {data.get('due_date') or 'Non renseignée'}")
                        st.markdown(f"**Taux TVA :** {data.get('tva_rate', 0)}%")

                    st.markdown(f"**Description :** {data.get('description', '—')}")

                    if result.get("invoice_id"):
                        st.caption(f"ID Supabase : `{result['invoice_id']}`")

                else:
                    pipeline_status.update(label=f"⚠️ Arrêt à l'étape : {final_status}", state="error")
                    for err in result.get("errors", []):
                        st.error(err)

            except Exception as e:
                pipeline_status.update(label="❌ Erreur inattendue", state="error")
                st.error(f"Erreur inattendue : {e}")

# ─── Tab 2 : Historique ───────────────────────────────────────────────────────
with tab2:
    if st.button("🔄 Actualiser", use_container_width=True):
        st.session_state["refresh_invoices"] = True

    if st.session_state.get("refresh_invoices", True):
        try:
            sb      = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            result  = sb.table(config.SUPABASE_TABLE).select("*").order("created_at", desc=True).execute()
            invoices = result.data

            if invoices:
                total_ttc = sum(i.get("amount_ttc", 0) for i in invoices)
                total_ht  = sum(i.get("amount_ht", 0) for i in invoices)
                total_tva = sum(i.get("tva_amount", 0) for i in invoices)

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("📄 Factures",    len(invoices))
                col2.metric("💰 Total HT",    f"{total_ht:,.2f} €")
                col3.metric("📊 Total TVA",   f"{total_tva:,.2f} €")
                col4.metric("💳 Total TTC",   f"{total_ttc:,.2f} €")

                st.markdown("---")

                for inv in invoices:
                    with st.expander(f"🧾 {inv.get('supplier_name', '—')} — {inv.get('invoice_date', '—')} — {inv.get('amount_ttc', 0):,.2f} €"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**N° Facture :** {inv.get('invoice_number', '—')}")
                            st.markdown(f"**Fournisseur :** {inv.get('supplier_name', '—')}")
                            st.markdown(f"**SIRET :** {inv.get('supplier_siret') or '—'}")
                            st.markdown(f"**Catégorie :** {inv.get('category', '—')}")
                        with col2:
                            st.markdown(f"**HT :** {inv.get('amount_ht', 0):,.2f} €")
                            st.markdown(f"**TVA ({inv.get('tva_rate', 0)}%) :** {inv.get('tva_amount', 0):,.2f} €")
                            st.markdown(f"**TTC :** {inv.get('amount_ttc', 0):,.2f} €")
                            st.markdown(f"**Échéance :** {inv.get('due_date') or '—'}")
                        st.markdown(f"**Description :** {inv.get('description', '—')}")
            else:
                st.info("Aucune facture enregistrée pour l'instant.")

        except Exception as e:
            st.error(f"Erreur chargement historique : {e}")

        st.session_state["refresh_invoices"] = False

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 17 — Automatisation comptable · [GitHub](https://github.com/Rek1DSables/templates-ai)")