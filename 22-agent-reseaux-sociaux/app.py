import streamlit as st
from graph import run_social_media
import config

st.set_page_config(
    page_title="Agent Réseaux Sociaux",
    page_icon="📱",
    layout="wide",
)

st.title("📱 Agent Réseaux Sociaux")
st.caption(f"LangGraph · Serper · `{config.MODEL_NAME}`")
st.markdown("---")

st.info(
    "Générez des posts adaptés à chaque plateforme + un planning de publication hebdomadaire.",
    icon="ℹ️",
)

with st.form("social_form"):
    st.subheader("📝 Paramètres")

    col1, col2 = st.columns(2)
    with col1:
        topic     = st.text_input("Sujet *", placeholder="Lancement de notre nouveau service IA")
        tone      = st.selectbox("Tonalité", config.TONES)
    with col2:
        objective = st.selectbox("Objectif", ["Notoriété", "Engagement", "Conversion", "Éducation"])
        platforms = st.multiselect("Plateformes *", config.PLATFORMS, default=["LinkedIn"])

    submitted = st.form_submit_button("🚀 Générer les posts", use_container_width=True, type="primary")

if submitted:
    if not topic or not platforms:
        st.error("⚠️ Le sujet et au moins une plateforme sont obligatoires.")
        st.stop()

    with st.status("⚙️ Génération en cours...", expanded=True) as pipeline_status:
        st.write("🔍 Recherche des tendances...")
        st.write("✍️ Rédaction des posts...")
        st.write("📅 Génération du planning...")

        try:
            result = run_social_media(
                topic     = topic,
                platforms = platforms,
                tone      = tone,
                objective = objective,
            )

            if result["status"] == "error":
                pipeline_status.update(label="❌ Erreur", state="error")
                for err in result["errors"]:
                    st.error(err)

            elif result["status"] == "completed":
                pipeline_status.update(label="✅ Posts générés !", state="complete", expanded=False)

                # Tendances
                if result.get("trending_topics"):
                    with st.expander("🔥 Tendances détectées", expanded=False):
                        for t in result["trending_topics"]:
                            st.markdown(f"- {t}")

                st.markdown("---")

                # Posts par plateforme
                st.subheader("📱 Posts générés")
                posts = result.get("posts", [])
                for post in posts:
                    platform_icons = {
                        "LinkedIn": "💼", "Twitter/X": "🐦",
                        "Instagram": "📸", "Facebook": "👥"
                    }
                    icon = platform_icons.get(post["platform"], "📱")

                    with st.expander(f"{icon} {post['platform']}", expanded=True):
                        st.text_area("Contenu", value=post["content"], height=150, key=f"post_{post['platform']}")

                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Hashtags :** {' '.join(['#' + h for h in post.get('hashtags', [])])}")
                        with col2:
                            st.markdown(f"**Meilleur moment :** {post.get('best_time', '—')}")

                        st.info(f"💡 {post.get('tip', '')}", icon="💡")

                # Planning
                st.markdown("---")
                st.subheader("📅 Planning hebdomadaire")
                planning = result.get("planning", [])
                if planning:
                    for p in planning:
                        col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
                        col1.write(f"**{p.get('day', '—')}**")
                        col2.write(p.get("time", "—"))
                        col3.write(p.get("platform", "—"))
                        col4.write(p.get("content_preview", "—")[:80] + "...")

                # Export
                export = "\n\n".join([
                    f"=== {p['platform']} ===\n{p['content']}\nHashtags : {' '.join(['#' + h for h in p.get('hashtags', [])])}\nMeilleur moment : {p.get('best_time', '—')}"
                    for p in posts
                ])
                st.download_button(
                    label="⬇️ Télécharger les posts",
                    data=export,
                    file_name=f"posts_{topic[:20].replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

                if result.get("errors"):
                    with st.expander("⚠️ Avertissements"):
                        for err in result["errors"]:
                            st.warning(err)

        except Exception as e:
            pipeline_status.update(label="❌ Erreur inattendue", state="error")
            st.error(f"Erreur inattendue : {e}")

st.markdown("---")
st.caption("Template 22 — Agent réseaux sociaux · [GitHub](https://github.com/Rek1DSables/templates-ai)")