# app.py
import streamlit as st
from graph import build_graph
from config import SUPPORTED_AUDIO_FORMATS

# --- UI ---
st.set_page_config(page_title="Agent Vocal Entrant AI", page_icon="🎙️", layout="centered")
st.title("🎙️ Agent Vocal Entrant AI")
st.caption("Transcription Whisper → Analyse intention Claude → Reponse vocale ElevenLabs")

st.info("Uploadez un fichier audio simulant un appel entrant. L'agent transcrit, analyse et repond vocalement.")

fichier = st.file_uploader(
    f"Fichier audio ({', '.join(SUPPORTED_AUDIO_FORMATS)})",
    type=SUPPORTED_AUDIO_FORMATS,
)

if fichier:
    st.audio(fichier, format=f"audio/{fichier.name.split('.')[-1]}")

    if st.button("Traiter l'appel", use_container_width=True):
        audio_bytes = fichier.read()
        audio_format = fichier.name.split(".")[-1].lower()

        with st.spinner("Transcription en cours (Whisper)..."):
            graph = build_graph()
            try:
                result = graph.invoke({
                    "audio_bytes": audio_bytes,
                    "audio_format": audio_format,
                    "transcription": "",
                    "intention": "",
                    "categorie": "",
                    "reponse_texte": "",
                    "audio_reponse": b"",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success("Appel traite avec succes !")

            col1, col2 = st.columns(2)
            col1.metric("Categorie", result["categorie"].upper())
            col2.metric("Intention", result["intention"][:50] + "..." if len(result["intention"]) > 50 else result["intention"])

            st.divider()

            tab1, tab2, tab3 = st.tabs(["Reponse vocale", "Transcription", "Analyse"])

            with tab1:
                if result["audio_reponse"]:
                    st.audio(result["audio_reponse"], format="audio/mp3")
                    st.download_button(
                        label="Telecharger la reponse audio",
                        data=result["audio_reponse"],
                        file_name="reponse_agent.mp3",
                        mime="audio/mp3",
                        use_container_width=True,
                    )
                st.text_area("Texte de la reponse", value=result["reponse_texte"], height=150)

            with tab2:
                st.text_area("Transcription Whisper", value=result["transcription"], height=200)

            with tab3:
                st.json({
                    "categorie": result["categorie"],
                    "intention": result["intention"],
                })