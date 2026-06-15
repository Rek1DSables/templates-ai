# app.py
import json
import streamlit as st
import pandas as pd
import plotly.express as px
from graph import build_graph
from config import SECTEURS_CIBLES, POSTES_CIBLES, TAILLES_ENTREPRISE, OBJECTIFS_SEQUENCE, SQL_SETUP

PROSPECTS_DEMO = [
    {"prenom": "Alexandre", "nom": "Petit", "email": "alexandre.petit@fintech-plus.fr", "entreprise": "FintechPlus", "poste": "CEO / Directeur Général", "secteur": "Fintech", "taille_entreprise": "PME (10-250 salariés)", "site_web": "fintech-plus.fr", "linkedin": "linkedin.com/in/alexandrepetit"},
    {"prenom": "Marie", "nom": "Leclerc", "email": "marie.leclerc@cabinet-ml.fr", "entreprise": "Cabinet ML Avocats", "poste": "Directeur des Opérations", "secteur": "Juridique / Cabinet d'avocats", "taille_entreprise": "PME (10-250 salariés)", "site_web": "cabinet-ml.fr", "linkedin": ""},
    {"prenom": "Thomas", "nom": "Bernard", "email": "thomas@saas-connect.io", "entreprise": "SaaSConnect", "poste": "CTO / Directeur Technique", "secteur": "SaaS B2B", "taille_entreprise": "TPE (1-10 salariés)", "site_web": "saas-connect.io", "linkedin": "linkedin.com/in/thomasbernard"},
    {"prenom": "Claire", "nom": "Rousseau", "email": "c.rousseau@industrie-cr.fr", "entreprise": "IndustrieCR", "poste": "Directeur Commercial", "secteur": "Industrie / Manufacturing", "taille_entreprise": "ETI (250-5000 salariés)", "site_web": "industrie-cr.fr", "linkedin": ""},
    {"prenom": "Lucas", "nom": "Moreau", "email": "l.moreau@consult-ai.fr", "entreprise": "ConsultAI", "poste": "CEO / Directeur Général", "secteur": "Conseil / ESN", "taille_entreprise": "PME (10-250 salariés)", "site_web": "consult-ai.fr", "linkedin": "linkedin.com/in/lucasmoreau"},
]

SEGMENT_LABELS = {
    "hot":  ("Prioritaire",    "🔴"),
    "warm": ("Haute priorité", "🟠"),
    "cold": ("Basse priorité", "🟢"),
}

st.set_page_config(page_title="Agent SDR / Revenue", page_icon="🎯", layout="centered")
st.title("🎯 Agent SDR / Revenue")
st.caption("Pipeline multi-agents : Enrichissement → Scoring → Séquence personnalisée → Envoi Gmail")

with st.expander("📋 Architecture du pipeline"):
    st.markdown("""
**4 agents spécialisés en séquence :**
1. **Agent Enrichissement** — recherche web (Serper) + qualification IA par prospect
2. **Agent Scoring** — score 0-100, segmentation Prioritaire / Haute priorité / Basse priorité, sauvegarde Supabase
3. **Agent Séquence** — génère 3 emails personnalisés par prospect (Prioritaire + Haute priorité uniquement)
4. **Agent Envoi** — envoie le premier email via Gmail (optionnel)
    """)

with st.expander("🗄️ Setup Supabase"):
    st.code(SQL_SETUP, language="sql")

st.divider()
st.subheader("Configuration de votre client idéal & Campagne")

col1, col2 = st.columns(2)
with col1:
    icp_secteurs = st.multiselect("Secteurs cibles", SECTEURS_CIBLES, default=["SaaS B2B", "Fintech", "Conseil / ESN"])
    icp_tailles = st.multiselect("Tailles d'entreprise", TAILLES_ENTREPRISE, default=["PME (10-250 salariés)", "ETI (250-5000 salariés)"])

with col2:
    icp_postes = st.multiselect("Postes cibles", POSTES_CIBLES, default=["CEO / Directeur Général", "CTO / Directeur Technique", "Directeur Commercial"])
    objectif = st.selectbox("Objectif de la séquence", OBJECTIFS_SEQUENCE)

col3, col4 = st.columns(2)
with col3:
    expediteur_nom = st.text_input("Votre nom", placeholder="Jean Martin")
with col4:
    expediteur_poste = st.text_input("Votre poste", placeholder="Consultant AI Automation")

produit_contexte = st.text_area(
    "Contexte produit / offre",
    placeholder="Ex : J'aide les PME B2B à automatiser leur qualification de leads avec des agents IA sur mesure. ROI moyen : 3h économisées par semaine, +30% de leads qualifiés.",
    height=80,
)

st.divider()
st.subheader("Liste de prospects")

source = st.radio("Source", ["Mode démo (5 prospects)", "Upload CSV"], horizontal=True)

prospects = []
if source == "Mode démo (5 prospects)":
    prospects = PROSPECTS_DEMO
    st.dataframe(pd.DataFrame(prospects), use_container_width=True, hide_index=True)
else:
    st.caption("Colonnes requises : prenom, nom, email, entreprise, poste, secteur, taille_entreprise, site_web")
    template = pd.DataFrame([{
        "prenom": "", "nom": "", "email": "", "entreprise": "",
        "poste": "", "secteur": "", "taille_entreprise": "", "site_web": "",
    }])
    st.download_button("📥 Template CSV", data=template.to_csv(index=False),
        file_name="template_prospects.csv", mime="text/csv")
    fichier = st.file_uploader("Upload CSV", type=["csv"])
    if fichier:
        df = pd.read_csv(fichier)
        prospects = df.to_dict(orient="records")
        st.success(f"{len(prospects)} prospects chargés")
        st.dataframe(df, use_container_width=True, hide_index=True)

st.divider()
envoyer = st.toggle("Envoyer le premier email via Gmail", value=False)
if envoyer:
    st.warning("⚠️ Les emails seront envoyés réellement depuis ta boîte Gmail.")

if st.button("Lancer le pipeline", use_container_width=True):
    if not prospects:
        st.error("Merci de fournir des prospects.")
    elif not expediteur_nom or not produit_contexte:
        st.error("Merci de renseigner votre nom et le contexte produit.")
    else:
        with st.spinner(f"Pipeline en cours — {len(prospects)} prospects..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "prospects": prospects,
                    "icp_secteurs": icp_secteurs,
                    "icp_postes": icp_postes,
                    "icp_tailles": icp_tailles,
                    "objectif_sequence": objectif,
                    "produit_contexte": produit_contexte,
                    "expediteur_nom": expediteur_nom,
                    "expediteur_poste": expediteur_poste,
                    "envoyer_emails": envoyer,
                    "prospects_enrichis": [],
                    "prospects_qualifies": [],
                    "sequences_generees": [],
                    "stats": {},
                    "audit_log": [],
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        stats = result["stats"]
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total", stats.get("total", 0))
        col2.metric("🔴 Prioritaire", stats.get("hot", 0))
        col3.metric("🟠 Haute priorité", stats.get("warm", 0))
        col4.metric("Score moyen", f"{stats.get('score_moyen', 0)}/100")

        st.divider()

        tab1, tab2, tab3, tab4 = st.tabs([
            "Scoring prospects",
            "Séquences emails",
            "Audit Trail",
            "Export",
        ])

        with tab1:
            qualifies = result["prospects_qualifies"]
            if qualifies:
                rows = []
                for p in qualifies:
                    seg = p.get("segment", "cold")
                    label, icone = SEGMENT_LABELS.get(seg, ("Basse priorité", "🟢"))
                    rows.append({
                        "Prospect": f"{p.get('prenom', '')} {p.get('nom', '')}",
                        "Entreprise": p.get("entreprise", ""),
                        "Poste": p.get("poste", ""),
                        "Score": p.get("score_icp", 0),
                        "Priorité": f"{icone} {label}",
                    })
                df_scores = pd.DataFrame(rows)
                st.dataframe(df_scores, use_container_width=True, hide_index=True)

                fig = px.bar(df_scores, x="Prospect", y="Score",
                    color="Score", color_continuous_scale="RdYlGn",
                    title="Score de correspondance par prospect")
                st.plotly_chart(fig, use_container_width=True)

                st.divider()
                for p in qualifies:
                    seg = p.get("segment", "cold")
                    label, icone = SEGMENT_LABELS.get(seg, ("Basse priorité", "🟢"))
                    with st.expander(f"{icone} {p.get('prenom', '')} {p.get('nom', '')} — {p.get('entreprise', '')} — {p.get('score_icp', 0)}/100 — {label}"):
                        st.markdown(f"**Résumé :** {p.get('resume_enrichi', '')}")
                        st.markdown(f"**Angle d'approche :** {p.get('angle_approche', '')}")
                        st.markdown(f"**Objection probable :** {p.get('objection_probable', '')}")
                        if p.get("signaux_detectes"):
                            st.markdown("**Signaux détectés :**")
                            for s in p["signaux_detectes"]:
                                st.markdown(f"- {s}")

        with tab2:
            sequences = result["sequences_generees"]
            if not sequences:
                st.info("Aucune séquence générée — tous les prospects sont classés en basse priorité.")
            for seq in sequences:
                prospect = seq["prospect"]
                emails = seq["emails"]
                seg = prospect.get("segment", "cold")
                label, icone = SEGMENT_LABELS.get(seg, ("Basse priorité", "🟢"))
                with st.expander(f"{icone} {prospect.get('prenom', '')} {prospect.get('nom', '')} — {prospect.get('entreprise', '')} — {label}"):
                    for key, lbl in [("email_1", "Email 1 — Premier contact"), ("email_2", "Email 2 — Relance J+5"), ("email_3", "Email 3 — Breakup J+12")]:
                        email_data = emails.get(key, {})
                        st.markdown(f"**{lbl}**")
                        st.markdown(f"Objet : `{email_data.get('sujet', '')}`")
                        st.text_area("", value=email_data.get("corps", ""), height=120, key=f"{prospect.get('email', '')}_{key}")
                        st.divider()

        with tab3:
            for entry in result["audit_log"]:
                detail = entry.get("detail", "")
                suffix = f" | {detail}" if detail else ""
                st.markdown(f"✅ `{entry.get('timestamp')}` **{entry.get('agent')}** — {entry.get('etape')}{suffix}")

        with tab4:
            col_a, col_b = st.columns(2)
            with col_a:
                if result["prospects_qualifies"]:
                    df_export = pd.DataFrame(result["prospects_qualifies"])
                    st.download_button(
                        label="📊 Prospects qualifiés CSV",
                        data=df_export.to_csv(index=False, encoding="utf-8"),
                        file_name="prospects_qualifies.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
            with col_b:
                st.download_button(
                    label="📦 Pipeline complet JSON",
                    data=json.dumps({
                        "stats": result["stats"],
                        "prospects": result["prospects_qualifies"],
                        "sequences": result["sequences_generees"],
                        "audit_log": result["audit_log"],
                    }, ensure_ascii=False, indent=2),
                    file_name="sdr_pipeline.json",
                    mime="application/json",
                    use_container_width=True,
                )