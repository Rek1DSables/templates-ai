# app.py
import base64
import streamlit as st
from graph import build_graph
from config import SUPPORTED_FORMATS, MAX_FILE_SIZE_MB

MEDIA_TYPES = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "gif": "image/gif",
    "webp": "image/webp",
}


def encoder_image(fichier) -> tuple[str, str]:
    extension = fichier.name.split(".")[-1].lower()
    media_type = MEDIA_TYPES.get(extension, "image/jpeg")
    image_bytes = fichier.read()
    image_base64 = base64.standard_b64encode(image_bytes).decode("utf-8")
    return image_base64, media_type


# --- UI ---
st.set_page_config(page_title="Analyseur d'Images AI", page_icon="🖼️", layout="centered")
st.title("🖼️ Analyseur d'Images & Documents Visuels AI")
st.caption("Description, extraction de donnees et insights depuis n'importe quelle image")

fichier = st.file_uploader(
    f"Uploade une image ({', '.join(SUPPORTED_FORMATS)}, max {MAX_FILE_SIZE_MB}MB)",
    type=SUPPORTED_FORMATS,
)

if fichier:
    taille_mb = fichier.size / (1024 * 1024)
    if taille_mb > MAX_FILE_SIZE_MB:
        st.error(f"Fichier trop lourd ({taille_mb:.1f}MB). Maximum : {MAX_FILE_SIZE_MB}MB.")
    else:
        st.image(fichier, caption=fichier.name, use_container_width=True)

        if st.button("Analyser l'image", use_container_width=True):
            fichier.seek(0)
            image_base64, media_type = encoder_image(fichier)

            with st.spinner("Analyse en cours : description, extraction, insights..."):
                try:
                    graph = build_graph()
                    result = graph.invoke({
                        "image_base64": image_base64,
                        "media_type": media_type,
                        "nom_fichier": fichier.name,
                        "description": "",
                        "donnees_extraites": "",
                        "insights": "",
                        "erreur": "",
                    })
                except Exception as e:
                    st.error(f"Erreur graph : {e}")
                    st.stop()

            if result["erreur"]:
                st.error(result["erreur"])
            else:
                st.success("Analyse terminee !")

                tab1, tab2, tab3 = st.tabs(["Description", "Donnees extraites", "Insights"])

                with tab1:
                    st.text_area("Description detaillee", value=result["description"], height=300)

                with tab2:
                    st.text_area("Donnees structurees", value=result["donnees_extraites"], height=300)

                with tab3:
                    st.text_area("Insights & recommandations", value=result["insights"], height=300)