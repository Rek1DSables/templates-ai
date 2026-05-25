import streamlit as st
from graph import generate_quiz, evaluate_quiz
import config

st.set_page_config(
    page_title="Formation & Quiz Adaptatif",
    page_icon="🎓",
    layout="centered",
)

st.title("🎓 Agent de Formation & Quiz Adaptatif")
st.caption(f"LangGraph · Supabase · `{config.MODEL_NAME}`")
st.markdown("---")

# ─── Session state ───────────────────────────────────────────────────────────
if "quiz_state" not in st.session_state:
    st.session_state.quiz_state = None
if "phase" not in st.session_state:
    st.session_state.phase = "setup"   # setup | quiz | results

# ─── Phase 1 : Setup ─────────────────────────────────────────────────────────
if st.session_state.phase == "setup":
    st.info(
        "Le quiz adaptatif va :\n"
        "1. Générer des questions adaptées à votre niveau\n"
        "2. Évaluer vos réponses\n"
        "3. Générer un feedback personnalisé\n"
        "4. Recommander le niveau suivant",
        icon="ℹ️",
    )

    with st.form("setup_form"):
        st.subheader("📋 Paramètres du quiz")

        col1, col2 = st.columns(2)
        with col1:
            learner_name = st.text_input("Votre prénom *", placeholder="Marie")
        with col2:
            current_level = st.selectbox("Niveau actuel", config.LEVELS)

        topic = st.text_input(
            "Sujet du quiz *",
            placeholder="Ex : Python, Marketing Digital, Excel, Comptabilité..."
        )

        submitted = st.form_submit_button("🚀 Générer le quiz", use_container_width=True, type="primary")

    if submitted:
        if not learner_name or not topic:
            st.error("⚠️ Le prénom et le sujet sont obligatoires.")
        else:
            with st.spinner("🤖 Génération des questions en cours..."):
                result = generate_quiz(
                    learner_name  = learner_name,
                    topic         = topic,
                    current_level = current_level,
                )

                if result["status"] == "error":
                    for err in result["errors"]:
                        st.error(err)
                else:
                    st.session_state.quiz_state = result
                    st.session_state.phase      = "quiz"
                    st.rerun()

# ─── Phase 2 : Quiz ───────────────────────────────────────────────────────────
elif st.session_state.phase == "quiz":
    state     = st.session_state.quiz_state
    questions = state["questions"]

    st.subheader(f"📝 Quiz — {state['topic']} — Niveau {state['current_level']}")
    st.caption(f"Apprenant : {state['learner_name']} · {len(questions)} questions")
    st.markdown("---")

    with st.form("quiz_form"):
        answers = []
        for i, q in enumerate(questions):
            st.markdown(f"**Question {i+1} / {len(questions)}**")
            st.markdown(q["question"])

            answer = st.radio(
                f"Votre réponse",
                options=[opt[0] for opt in [o.split(".") for o in q["options"]]],
                key=f"q_{i}",
                horizontal=True,
                label_visibility="collapsed",
            )

            # Affiche les options
            for opt in q["options"]:
                st.markdown(f"&nbsp;&nbsp;{opt}")

            answers.append(answer)
            st.markdown("---")

        submitted = st.form_submit_button("✅ Soumettre mes réponses", use_container_width=True, type="primary")

    if submitted:
        with st.spinner("🤖 Évaluation en cours..."):
            result = evaluate_quiz(state, answers)

            if result["status"] == "error":
                for err in result["errors"]:
                    st.error(err)
            else:
                st.session_state.quiz_state = result
                st.session_state.phase      = "results"
                st.rerun()

# ─── Phase 3 : Résultats ──────────────────────────────────────────────────────
elif st.session_state.phase == "results":
    state     = st.session_state.quiz_state
    score     = state["score"]
    questions = state["questions"]
    answers   = state["answers"]

    st.subheader(f"📊 Résultats — {state['learner_name']}")
    st.markdown("---")

    # Score
    score_pct = int(score * 100)
    col1, col2, col3 = st.columns(3)
    col1.metric("🎯 Score",          f"{score_pct}%")
    col2.metric("✅ Bonnes réponses", f"{int(score * len(questions))}/{len(questions)}")
    col3.metric("📈 Niveau suivant", state.get("next_level", state["current_level"]))

    if score >= config.PASS_THRESHOLD:
        st.success(f"🎉 Félicitations ! Vous passez au niveau **{state['next_level']}** !")
    else:
        st.warning(f"💪 Continuez à pratiquer le niveau **{state['current_level']}** !")

    st.markdown("---")

    # Détail des réponses
    st.subheader("📋 Détail des réponses")
    for i, (q, a) in enumerate(zip(questions, answers)):
        is_correct = a.upper() == q["answer"].upper()
        icon = "✅" if is_correct else "❌"
        with st.expander(f"{icon} Question {i+1} — {q['question'][:60]}..."):
            st.markdown(f"**Votre réponse :** {a}")
            st.markdown(f"**Bonne réponse :** {q['answer']}")
            st.markdown(f"**Explication :** {q['explanation']}")

    st.markdown("---")

    # Feedback IA
    with st.expander("🤖 Feedback personnalisé", expanded=True):
        st.markdown(state.get("feedback", "—"))

    st.markdown("---")

    # Rejouer
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Nouveau quiz — même niveau", use_container_width=True):
            st.session_state.phase = "setup"
            st.session_state.quiz_state = None
            st.rerun()
    with col2:
        if st.button("⬆️ Passer au niveau suivant", use_container_width=True, type="primary"):
            new_state = {**state, "current_level": state["next_level"]}
            with st.spinner("Génération du quiz niveau supérieur..."):
                result = generate_quiz(
                    learner_name  = state["learner_name"],
                    topic         = state["topic"],
                    current_level = state["next_level"],
                )
                st.session_state.quiz_state = result
                st.session_state.phase      = "quiz"
                st.rerun()

# ─── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption("Template 20 — Formation & Quiz Adaptatif · [GitHub](https://github.com/Rek1DSables/templates-ai)")