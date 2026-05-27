# app.py
import streamlit as st
from graph import build_graph
from config import TECHNOLOGIES, NIVEAUX_URGENCE, TYPES_PROBLEME

URGENCE_CONFIG = {
    "Critique (production down)": ("🔴 CRITIQUE", "error"),
    "Haute (impact utilisateurs)": ("🟠 HAUTE", "warning"),
    "Normale (bug non bloquant)": ("🟡 NORMALE", "info"),
    "Basse (amelioration)": ("🟢 BASSE", "success"),
}

# --- UI ---
st.set_page_config(page_title="Agent Support Technique AI", page_icon="🛠️", layout="wide")
st.title("🛠️ Agent de Support Technique AI")
st.caption("Diagnostic → Solutions → Plan de resolution etape par etape")

with st.form("form_support"):
    col1, col2, col3 = st.columns(3)
    technologie = col1.selectbox("Technologie", TECHNOLOGIES)
    type_probleme = col2.selectbox("Type de probleme", TYPES_PROBLEME)
    urgence = col3.selectbox("Urgence", NIVEAUX_URGENCE)

    description = st.text_area(
        "Description du probleme",
        placeholder="Decris le probleme en detail : contexte, comportement attendu vs observe, depuis quand...",
        height=120,
    )

    logs = st.text_area(
        "Logs / Messages d'erreur (optionnel)",
        placeholder="Colle ici les messages d'erreur, stack traces, logs...",
        height=150,
    )

    code = st.text_area(
        "Code concerne (optionnel)",
        placeholder="Colle ici le code qui pose probleme...",
        height=150,
    )

    submit = st.form_submit_button("Analyser et resoudre", use_container_width=True)

if submit:
    if not description:
        st.error("Merci de decrire le probleme.")
    else:
        label, niveau = URGENCE_CONFIG.get(urgence, ("🟡 NORMALE", "info"))
        getattr(st, niveau)(f"Niveau d'urgence : {label}")

        with st.spinner("Diagnostic et generation du plan de resolution en cours..."):
            try:
                graph = build_graph()
                result = graph.invoke({
                    "technologie": technologie,
                    "type_probleme": type_probleme,
                    "urgence": urgence,
                    "description": description,
                    "logs": logs,
                    "code": code,
                    "diagnostic": "",
                    "solutions": "",
                    "plan_resolution": "",
                    "prevention": "",
                    "erreur": "",
                })
            except Exception as e:
                st.error(f"Erreur graph : {e}")
                st.stop()

        if result["erreur"]:
            st.warning(f"Avertissement : {result['erreur']}")
        else:
            st.success("Analyse terminee !")

            col1, col2 = st.columns(2)
            col1.metric("Technologie", technologie)
            col2.metric("Type", type_probleme)

            st.divider()

            tab1, tab2, tab3 = st.tabs([
                "Plan de resolution",
                "Solutions",
                "Diagnostic",
            ])

            with tab1:
                st.markdown(result["plan_resolution"])

            with tab2:
                st.markdown(result["solutions"])

            with tab3:
                st.markdown(result["diagnostic"])