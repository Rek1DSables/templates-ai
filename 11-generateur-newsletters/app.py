import streamlit as st
from graph import preview_newsletter, run_newsletter
from supabase import create_client
import config

st.set_page_config(
    page_title="Générateur de Newsletters",
    page_icon="📧",
    layout="centered",
)

st.title("📧 Générateur de Newsletters Automatiques")
st.caption(f"LangGraph · Gmail · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

tab1, tab2 = st.tabs(["✍️ Créer & Envoyer", "👥 Abonnés"])

# ─── Tab 1 : Créer & Envoyer ─────────────────────────────────────────────────
with tab1:
    with st.form("newsletter_form"):
        st.subheader("📝 Paramètres")

        topic    = st.text_input("Sujet *", placeholder="Les tendances IA en 2026")
        audience = st.text_input("Audience *", placeholder="Dirigeants de PME françaises")
        tone     = st.selectbox("Tonalité", config.TONES)
        key_points = st.text_area(
            "Points clés à aborder *",
            height=100,
            placeholder="1. L'IA générative transforme les PME\n2. Les outils no-code accessibles\n3. ROI concret en 3 mois"
        )

        col1, col2 = st.columns(2)
        with col1:
            preview_btn = st.form_submit_button("👁️ Prévisualiser", use_container_width=True)
        with col2:
            send_btn = st.form_submit_button("🚀 Générer & Envoyer", use_container_width=True, type="primary")

    if preview_btn or send_btn:
        if not topic or not audience or not key_points:
            st.error("⚠️ Tous les champs marqués * sont obligatoires.")
            st.stop()

        if preview_btn:
            with st.spinner("🤖 Génération en cours..."):
                result = preview_newsletter(topic, tone, audience, key_points)

                if result["status"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.success("✅ Prévisualisation générée !")
                    st.markdown(f"**Objet :** {result.get('subject', '—')}")
                    st.markdown("---")
                    st.markdown(result.get("content", "—"))

        if send_btn:
            with st.status("⚙️ Envoi en cours...", expanded=True) as pipeline_status:
                st.write("🤖 Génération du contenu...")
                st.write("👥 Récupération des abonnés...")
                st.write("📧 Envoi en cours...")

                result = run_newsletter(topic, tone, audience, key_points)

                if result["status"] == "error":
                    pipeline_status.update(label="❌ Erreur", state="error")
                    for err in result["errors"]:
                        st.error(err)
                else:
                    pipeline_status.update(label=f"✅ {result['sent_count']} emails envoyés !", state="complete", expanded=False)
                    st.success(f"✅ Newsletter envoyée à **{result['sent_count']}** abonnés.")

                    st.markdown(f"**Objet :** {result.get('subject', '—')}")
                    with st.expander("📧 Contenu envoyé"):
                        st.markdown(result.get("content", "—"))

                    if result.get("errors"):
                        with st.expander("⚠️ Erreurs d'envoi"):
                            for err in result["errors"]:
                                st.warning(err)

# ─── Tab 2 : Abonnés ─────────────────────────────────────────────────────────
with tab2:
    st.subheader("👥 Gestion des abonnés")

    with st.form("add_subscriber"):
        col1, col2 = st.columns(2)
        with col1:
            sub_name  = st.text_input("Nom", placeholder="Marie Dupont")
        with col2:
            sub_email = st.text_input("Email *", placeholder="marie@dupont.fr")
        add_btn = st.form_submit_button("➕ Ajouter", use_container_width=True)

    if add_btn:
        if not sub_email:
            st.error("⚠️ L'email est obligatoire.")
        else:
            try:
                sb = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
                sb.table(config.SUPABASE_TABLE).insert({
                    "name":   sub_name,
                    "email":  sub_email,
                    "active": True,
                }).execute()
                st.success(f"✅ {sub_email} ajouté !")
            except Exception as e:
                st.error(f"Erreur : {e}")

    st.markdown("---")

    try:
        sb     = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        result = sb.table(config.SUPABASE_TABLE).select("*").order("created_at", desc=True).execute()
        subs   = result.data

        if subs:
            actifs = len([s for s in subs if s.get("active")])
            st.metric("Abonnés actifs", actifs)
            st.markdown("---")
            for s in subs:
                col1, col2, col3 = st.columns([3, 2, 1])
                col1.write(s.get("name") or "—")
                col2.write(s.get("email"))
                col3.write("✅" if s.get("active") else "❌")
        else:
            st.info("Aucun abonné pour l'instant.")
    except Exception as e:
        st.error(f"Erreur chargement : {e}")

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 21 — Générateur de newsletters · [GitHub](https://github.com/Rek1DSables/templates-ai)")