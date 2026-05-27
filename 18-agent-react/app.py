# app.py
import streamlit as st
from graph import build_graph
from config import MAX_ITERATIONS

# --- UI ---
st.set_page_config(page_title="Agent ReAct Autonome", page_icon="🤖", layout="centered")
st.title("🤖 Agent de Recherche Autonome ReAct")
st.caption("L'agent raisonne et recherche en boucle jusqu'a trouver une reponse complete")

question = st.text_area(
    "Question complexe",
    placeholder="Quelles sont les differences entre LangGraph et CrewAI pour un projet de production en 2025 ?",
    height=100,
)

if st.button("Lancer l'agent", use_container_width=True):
    if not question.strip():
        st.error("Merci de poser une question.")
    else:
        with st.spinner("Agent en cours de raisonnement..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "question": question,
                    "historique": [],
                    "iteration": 0,
                    "pensee": "",
                    "action": "",
                    "observation": "",
                    "reponse_finale": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.error(result["erreur"])
        else:
            st.success(f"Reponse trouvee en {result['iteration']} iteration(s)")

            tab1, tab2 = st.tabs(["Reponse finale", "Raisonnement detaille"])

            with tab1:
                if result["reponse_finale"]:
                    st.markdown(result["reponse_finale"])
                else:
                    st.warning("Iterations maximum atteintes sans reponse finale.")
                    if result["historique"]:
                        derniere = [e for e in result["historique"] if e.startswith("OBSERVATION")]
                        if derniere:
                            st.text_area("Derniere observation", value=derniere[-1], height=200)

            with tab2:
                st.caption(f"Iterations : {result['iteration']} / {MAX_ITERATIONS}")
                for i, etape in enumerate(result["historique"]):
                    if etape.startswith("PENSEE"):
                        st.info(etape)
                    elif etape.startswith("ACTION"):
                        st.warning(etape)
                    elif etape.startswith("OBSERVATION"):
                        st.success(etape)
                    elif etape.startswith("REPONSE"):
                        st.markdown(f"**{etape}**")