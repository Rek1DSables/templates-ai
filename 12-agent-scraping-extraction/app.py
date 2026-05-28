# app.py
import json
import streamlit as st
from graph import build_graph
from config import MODES_EXTRACTION, TYPES_EXTRACTION, FORMATS_SORTIE


# --- UI ---
st.set_page_config(page_title="Agent Scraping & Extraction", page_icon="🕷️", layout="centered")
st.title("🕷️ Agent Scraping & Extraction")
st.caption("Extrait des données structurées depuis des URLs ou du texte brut")

mode = st.radio("Mode", MODES_EXTRACTION, horizontal=True)
type_extraction = st.selectbox("Type de données à extraire", TYPES_EXTRACTION)

champs_personnalises = []
if "personnalisées" in type_extraction:
    champs_str = st.text_input(
        "Champs à extraire (séparés par des virgules)",
        placeholder="nom, email, ville, secteur"
    )
    champs_personnalises = [c.strip() for c in champs_str.split(",") if c.strip()]

urls = []
texte_brut = ""

if mode == "Extraire depuis une URL":
    url = st.text_input("URL à scraper", placeholder="https://example.com")
    if url:
        urls = [url]

elif mode == "Extraire depuis une liste d'URLs":
    urls_str = st.text_area(
        "Liste d'URLs (une par ligne, max 5)",
        placeholder="https://site1.com\nhttps://site2.com",
        height=120,
    )
    urls = [u.strip() for u in urls_str.split("\n") if u.strip()][:5]
    if urls:
        st.caption(f"{len(urls)} URL(s) détectée(s)")

else:
    texte_brut = st.text_area(
        "Texte brut à analyser",
        placeholder="Colle ici le contenu depuis lequel extraire les données...",
        height=250,
    )

if st.button("Extraire les données", use_container_width=True):
    if not urls and not texte_brut:
        st.error("Merci de fournir une URL ou du texte.")
    else:
        with st.spinner("Scraping et extraction en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "mode": mode,
                    "urls": urls,
                    "texte_brut": texte_brut,
                    "type_extraction": type_extraction,
                    "champs_personnalises": champs_personnalises,
                    "contenu_scrape": {},
                    "donnees_extraites": [],
                    "nb_resultats": 0,
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(result["erreur"])

        donnees = result["donnees_extraites"]
        st.metric("Résultats extraits", result["nb_resultats"])

        if not donnees:
            st.warning("Aucune donnée extraite. Essaie une autre URL ou un autre type d'extraction.")
        else:
            st.divider()

            for item in donnees:
                source = item.get("_source", "")
                champs = {k: v for k, v in item.items() if k != "_source" and v}

                with st.container(border=True):
                    champs_liste = list(champs.items())

                    if champs_liste:
                        # Premier champ en titre
                        titre_key, titre_val = champs_liste[0]
                        col_titre, col_source = st.columns([4, 1])
                        with col_titre:
                            st.markdown(f"**{titre_val}**")
                        with col_source:
                            if source:
                                st.caption(f"🔗 {source[:30]}...")

                        # Autres champs
                        for k, v in champs_liste[1:]:
                            st.markdown(f"**{k.capitalize()}** : {v}")

            st.divider()
            st.markdown("**Télécharger les données**")

            col1, col2 = st.columns(2)

            with col1:
                json_str = json.dumps(donnees, ensure_ascii=False, indent=2)
                st.download_button(
                    label="📦 Télécharger JSON",
                    data=json_str,
                    file_name="extraction.json",
                    mime="application/json",
                    use_container_width=True,
                )

            with col2:
                try:
                    import pandas as pd
                    df = pd.DataFrame(donnees)
                    csv_str = df.to_csv(index=False, encoding="utf-8")
                    st.download_button(
                        label="📊 Télécharger CSV",
                        data=csv_str,
                        file_name="extraction.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                except Exception as e:
                    st.warning(f"CSV indisponible : {e}")