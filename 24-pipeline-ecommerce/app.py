import streamlit as st
from graph import run_action
from supabase import create_client
import config

st.set_page_config(
    page_title="Pipeline E-commerce",
    page_icon="🛒",
    layout="wide",
)

st.title("🛒 Pipeline E-commerce Automatisé")
st.caption(f"LangGraph · Supabase · Gmail · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "➕ Nouvelle commande", "✏️ Mettre à jour", "🚨 Alertes"])

# ─── Tab 1 : Dashboard ────────────────────────────────────────────────────────
with tab1:
    if st.button("🔄 Actualiser", use_container_width=True):
        with st.spinner("Chargement..."):
            result = run_action("get_dashboard")

            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                orders   = result.get("orders", [])
                products = result.get("products", [])

                # Métriques
                total_ca     = sum(o.get("total", 0) for o in orders)
                total_orders = len(orders)
                pending      = len([o for o in orders if o["status"] == "En attente"])

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("💰 CA Total",       f"{total_ca:,.2f} €")
                col2.metric("📦 Commandes",      total_orders)
                col3.metric("⏳ En attente",     pending)
                col4.metric("🏷️ Produits",       len(products))

                st.markdown("---")

                with st.expander("🤖 Résumé IA", expanded=True):
                    st.markdown(result.get("summary", "—"))

                st.markdown("---")

                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📦 Commandes récentes")
                    for o in orders[:10]:
                        status_icon = {
                            "En attente": "⏳", "Confirmée": "✅",
                            "En préparation": "🔧", "Expédiée": "🚚",
                            "Livrée": "✅", "Annulée": "❌"
                        }.get(o["status"], "📦")
                        st.markdown(f"{status_icon} **{o['product_name']}** x{o['quantity']} — {o['total']}€ — {o['status']}")
                        st.caption(f"Client : {o['customer_name']} | `{o['id'][:8]}...`")

                with col2:
                    st.subheader("🏷️ Stock produits")
                    for p in products:
                        stock_icon = "🔴" if p["stock"] < config.LOW_STOCK_THRESHOLD else "🟢"
                        st.markdown(f"{stock_icon} **{p['name']}** — Stock : {p['stock']} — Prix : {p['price']}€")

# ─── Tab 2 : Nouvelle commande ────────────────────────────────────────────────
with tab2:
    with st.form("order_form"):
        st.subheader("👤 Client")
        col1, col2 = st.columns(2)
        with col1:
            customer_name  = st.text_input("Nom *", placeholder="Marie Dupont")
        with col2:
            customer_email = st.text_input("Email *", placeholder="marie@dupont.fr")

        st.subheader("🛍️ Produit")
        try:
            sb       = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
            products = sb.table(config.PRODUCTS_TABLE).select("*").execute().data
            product_options = {f"{p['name']} — {p['price']}€ (stock: {p['stock']})": p["id"] for p in products}
        except:
            product_options = {}

        selected_product = st.selectbox("Produit *", list(product_options.keys()) if product_options else ["Aucun produit"])
        quantity         = st.number_input("Quantité *", min_value=1, value=1)

        submitted = st.form_submit_button("🛒 Passer la commande", use_container_width=True, type="primary")

    if submitted:
        if not customer_name or not customer_email or not product_options:
            st.error("⚠️ Tous les champs sont obligatoires.")
        else:
            product_id = product_options[selected_product]
            with st.spinner("Traitement..."):
                result = run_action(
                    "new_order",
                    customer_name  = customer_name,
                    customer_email = customer_email,
                    product_id     = product_id,
                    quantity       = quantity,
                )
                if result["status_pipeline"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success(f"✅ Commande créée ! ID : `{result.get('order_id', '—')}`")

# ─── Tab 3 : Mettre à jour ────────────────────────────────────────────────────
with tab3:
    with st.form("update_form"):
        order_id   = st.text_input("ID commande *", placeholder="Copiez l'ID depuis le dashboard")
        new_status = st.selectbox("Nouveau statut *", config.ORDER_STATUSES)
        submitted  = st.form_submit_button("✏️ Mettre à jour", use_container_width=True, type="primary")

    if submitted:
        if not order_id:
            st.error("⚠️ L'ID est obligatoire.")
        else:
            result = run_action("update_status", order_id=order_id, new_status=new_status)
            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                st.success(f"✅ Statut mis à jour : **{new_status}**")

# ─── Tab 4 : Alertes ─────────────────────────────────────────────────────────
with tab4:
    if st.button("🔍 Vérifier les alertes", use_container_width=True, type="primary"):
        with st.spinner("Analyse en cours..."):
            result = run_action("check_alerts")

            if result["status_pipeline"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                alerts = result.get("alerts", [])

                if alerts:
                    st.metric("🚨 Alertes détectées", len(alerts))
                    st.markdown("---")
                    for a in alerts:
                        st.markdown(f"{a['level']} **{a['type']}** — {a['message']}")
                    if result.get("alert_sent"):
                        st.success("📧 Email d'alerte envoyé !")
                else:
                    st.success("✅ Aucune alerte — tout est nominal.")

st.markdown("---")
st.caption("Template 24 — Pipeline E-commerce · [GitHub](https://github.com/Rek1DSables/templates-ai)")