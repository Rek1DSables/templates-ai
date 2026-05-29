# app.py
import json
import io
import streamlit as st
import pandas as pd
from graph import build_graph
from config import OBJECTIFS, TONS


COLONNES_REQUISES = ["nom", "prenom", "email", "entreprise", "poste", "secteur", "info_perso"]

CONTACTS_DEMO = [
    {"nom": "Martin", "prenom": "Sophie", "email": "sophie@demo.com", "entreprise": "TechCorp", "poste": "Directrice Marketing", "secteur": "SaaS B2B", "info_perso": "A récemment levé 2M€"},
    {"nom": "Dupont", "prenom": "Thomas", "email": "thomas@demo.com", "entreprise": "RetailMax", "poste": "CEO", "secteur": "E-commerce", "info_perso": "Lance une nouvelle gamme produits"},
    {"nom": "Bernard", "prenom": "Claire", "email": "claire@demo.com", "entreprise": "FinanceX", "poste": "CFO", "secteur": "Finance", "info_perso": "Cherche à automatiser ses processus"},
    {"nom": "Leroy", "prenom": "Marc", "email": "marc@demo.com", "entreprise": "MediSanté", "poste": "DRH", "secteur": "Santé", "info_perso": "En pleine phase de recrutement"},
    {"nom": "Simon", "prenom": "Julie", "email": "julie@demo.com", "entreprise": "LogiPro", "poste": "COO", "secteur": "Logistique", "info_perso": "Problèmes de gestion opérationnelle"},
]


st.set_page_config(page_title="Agent Email en Masse", page_icon="📨", layout="centered")
st.title("📨 Agent Email en Masse")
st.caption("Upload liste contacts → Génération emails ultra-personnalisés → Envoi Gmail")

st.subheader("Paramètres de la campagne")

col1, col2 = st.columns(2)
with col1:
    objectif = st.selectbox("Objectif", OBJECTIFS)
    ton = st.selectbox("Ton", TONS)
with col2:
    expediteur_nom = st.text_input("Votre nom", placeholder="Jean Martin")
    contexte_produit = st.text_area(
        "Contexte produit / offre",
        placeholder="Ex : Nous aidons les PME à automatiser leur qualification de leads avec l'IA. ROI moyen : 3h économisées par semaine.",
        height=100,
    )

st.divider()
st.subheader("Liste de contacts")

source = st.radio("Source", ["Mode démo (5 contacts)", "Upload CSV", "Saisie manuelle"], horizontal=True)

contacts = []

if source == "Mode démo (5 contacts)":
    contacts = CONTACTS_DEMO
    st.dataframe(pd.DataFrame(contacts), use_container_width=True, hide_index=True)

elif source == "Upload CSV":
    st.caption("Colonnes attendues : nom, prenom, email, entreprise, poste, secteur, info_perso")

    template_csv = pd.DataFrame([{col: "" for col in COLONNES_REQUISES}])
    st.download_button(
        label="📥 Télécharger template CSV",
        data=template_csv.to_csv(index=False),
        file_name="template_contacts.csv",
        mime="text/csv",
    )

    fichier = st.file_uploader("Upload CSV contacts", type=["csv"])
    if fichier:
        try:
            df = pd.read_csv(fichier)
            for col in COLONNES_REQUISES:
                if col not in df.columns:
                    df[col] = ""
            contacts = df.to_dict(orient="records")
            st.success(f"{len(contacts)} contacts chargés")
            st.dataframe(df, use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"Erreur lecture CSV : {e}")

else:
    nb = st.number_input("Nombre de contacts", min_value=1, max_value=20, value=1)
    for i in range(nb):
        with st.expander(f"Contact #{i+1}"):
            c1, c2 = st.columns(2)
            nom = c1.text_input(f"Nom #{i+1}")
            prenom = c2.text_input(f"Prénom #{i+1}")
            email = c1.text_input(f"Email #{i+1}")
            entreprise = c2.text_input(f"Entreprise #{i+1}")
            poste = c1.text_input(f"Poste #{i+1}")
            secteur = c2.text_input(f"Secteur #{i+1}")
            info_perso = st.text_input(f"Info personnalisée #{i+1}", placeholder="Ex : vient de lever des fonds")
            contacts.append({
                "nom": nom, "prenom": prenom, "email": email,
                "entreprise": entreprise, "poste": poste,
                "secteur": secteur, "info_perso": info_perso,
            })

st.divider()
st.subheader("Envoi")
envoyer = st.toggle("Envoyer les emails via Gmail après génération", value=False)
if envoyer:
    st.warning("⚠️ Les emails seront envoyés réellement. Assure-toi que credentials.json et token.json sont présents.")

if st.button("Générer les emails", use_container_width=True):
    if not contacts:
        st.error("Merci de fournir au moins un contact.")
    elif not expediteur_nom or not contexte_produit:
        st.error("Merci de renseigner votre nom et le contexte produit.")
    else:
        with st.spinner(f"Génération de {len(contacts)} emails personnalisés..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "contacts": contacts,
                    "objectif": objectif,
                    "ton": ton,
                    "contexte_produit": contexte_produit,
                    "expediteur_nom": expediteur_nom,
                    "emails_generes": [],
                    "emails_envoyes": 0,
                    "emails_erreurs": 0,
                    "envoyer": envoyer,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        emails = result["emails_generes"]

        col1, col2, col3 = st.columns(3)
        col1.metric("Emails générés", len(emails))
        if envoyer:
            col2.metric("Envoyés", result["emails_envoyes"])
            col3.metric("Erreurs", result["emails_erreurs"])

        st.divider()

        for i, email in enumerate(emails):
            statut = email.get("statut", "")
            icone = "✅" if statut == "envoye" else "📝" if statut == "genere" else "❌"

            with st.expander(f"{icone} {email.get('prenom', '')} {email.get('nom', '')} — {email.get('entreprise', '')}"):
                st.markdown(f"**À :** {email.get('email', '—')}")
                st.markdown(f"**Objet :** {email.get('objet', '')}")
                st.divider()
                st.text_area(
                    "Corps de l'email",
                    value=email.get("corps", ""),
                    height=200,
                    key=f"email_{i}",
                )

        st.divider()

        # Export
        col_json, col_csv = st.columns(2)

        with col_json:
            json_str = json.dumps(emails, ensure_ascii=False, indent=2)
            st.download_button(
                label="📦 Télécharger JSON",
                data=json_str,
                file_name="emails_generes.json",
                mime="application/json",
                use_container_width=True,
            )

        with col_csv:
            try:
                df_export = pd.DataFrame(emails)
                csv_str = df_export.to_csv(index=False, encoding="utf-8")
                st.download_button(
                    label="📊 Télécharger CSV",
                    data=csv_str,
                    file_name="emails_generes.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            except Exception as e:
                st.warning(f"CSV indisponible : {e}")