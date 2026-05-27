import time
import json
from typing import TypedDict, Optional
from datetime import datetime, timezone

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from supabase import create_client

import config

# ─── LLM ─────────────────────────────────────────────────────────────────────
llm = ChatAnthropic(
    model=config.MODEL_NAME,
    api_key=config.ANTHROPIC_API_KEY,
    max_tokens=2048,
)

# ─── State ───────────────────────────────────────────────────────────────────
class QuizState(TypedDict):
    # Input
    learner_name:  str
    topic:         str
    current_level: str

    # Runtime
    questions:     Optional[list]   # liste de dicts {question, options, answer, explanation}
    answers:       Optional[list]   # réponses de l'apprenant
    score:         Optional[float]
    feedback:      Optional[str]
    next_level:    Optional[str]
    session_id:    Optional[str]

    # Suivi
    errors: list
    status: str

# ─── Helpers ─────────────────────────────────────────────────────────────────
def invoke_with_retry(chain, input_data):
    for attempt in range(config.MAX_RETRIES):
        try:
            return chain.invoke(input_data)
        except Exception as e:
            if "overloaded" in str(e).lower() and attempt < config.MAX_RETRIES - 1:
                time.sleep(config.RETRY_DELAY)
                continue
            raise

def _supabase():
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)

def _now():
    return datetime.now(timezone.utc).isoformat()

def _stop_on_error(next_node):
    def router(state):
        return END if state["status"] == "error" else next_node
    return router

# ─── Noeuds ──────────────────────────────────────────────────────────────────
def generate_questions(state: QuizState) -> QuizState:
    """Génère des questions adaptées au niveau de l'apprenant."""
    try:
        prompt = f"""Tu es un formateur expert. Génère un quiz adaptatif.

Apprenant : {state['learner_name']}
Sujet : {state['topic']}
Niveau : {state['current_level']}

Génère exactement {config.QUESTIONS_PER_SESSION} questions QCM adaptées au niveau {state['current_level']}.

Réponds UNIQUEMENT avec un JSON valide :
[
  {{
    "question": "texte de la question",
    "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
    "answer": "A",
    "explanation": "explication courte de la bonne réponse"
  }}
]

Les questions doivent être progressives — de la plus simple à la plus complexe pour ce niveau.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])
        content  = response.content.strip().replace("```json", "").replace("```", "").strip()
        questions = json.loads(content)

        return {**state, "questions": questions, "status": "questions_generated"}

    except Exception as e:
        return {**state, "errors": [f"Génération questions : {e}"], "status": "error"}


def evaluate_answers(state: QuizState) -> QuizState:
    """Évalue les réponses et calcule le score."""
    try:
        questions = state["questions"]
        answers   = state["answers"]

        if not answers or len(answers) != len(questions):
            return {**state, "errors": ["Nombre de réponses incorrect."], "status": "error"}

        correct = sum(
            1 for q, a in zip(questions, answers)
            if a.upper() == q["answer"].upper()
        )

        score = correct / len(questions)
        return {**state, "score": score, "status": "evaluated"}

    except Exception as e:
        return {**state, "errors": [f"Évaluation : {e}"], "status": "error"}


def generate_feedback(state: QuizState) -> QuizState:
    """Génère un feedback personnalisé et détermine le niveau suivant."""
    try:
        questions = state["questions"]
        answers   = state["answers"]
        score     = state["score"]

        # Détail des réponses
        details = []
        for i, (q, a) in enumerate(zip(questions, answers)):
            is_correct = a.upper() == q["answer"].upper()
            details.append(
                f"Q{i+1} : {'✅' if is_correct else '❌'} "
                f"Réponse : {a} | Correct : {q['answer']} | {q['explanation']}"
            )

        details_text = "\n".join(details)

        # Niveau suivant
        levels      = config.LEVELS
        current_idx = levels.index(state["current_level"]) if state["current_level"] in levels else 0

        if score >= config.PASS_THRESHOLD and current_idx < len(levels) - 1:
            next_level = levels[current_idx + 1]
        else:
            next_level = state["current_level"]

        prompt = f"""Tu es un formateur bienveillant. Génère un feedback personnalisé.

Apprenant : {state['learner_name']}
Sujet : {state['topic']}
Niveau actuel : {state['current_level']}
Score : {score*100:.0f}% ({int(score * len(questions))}/{len(questions)} bonnes réponses)
Niveau suivant recommandé : {next_level}

Détail des réponses :
{details_text}

Génère un feedback qui :
1. Félicite ou encourage selon le score
2. Identifie les points forts
3. Pointe les lacunes à combler
4. Recommande des ressources ou exercices pour progresser
5. Annonce le niveau suivant

Ton bienveillant et motivant. Français. 200 mots max.
"""
        response = invoke_with_retry(llm, [HumanMessage(content=prompt)])

        return {**state, "feedback": response.content, "next_level": next_level}

    except Exception as e:
        return {**state, "errors": [f"Feedback : {e}"], "status": "error"}


def save_session(state: QuizState) -> QuizState:
    """Enregistre la session dans Supabase."""
    try:
        result = _supabase().table(config.SUPABASE_TABLE).insert({
            "learner_name":  state["learner_name"],
            "topic":         state["topic"],
            "level":         state["current_level"],
            "score":         state["score"],
            "next_level":    state["next_level"],
            "questions":     json.dumps(state["questions"]),
            "answers":       json.dumps(state["answers"]),
            "feedback":      state["feedback"],
            "created_at":    _now(),
        }).execute()

        session_id = result.data[0]["id"]
        return {**state, "session_id": session_id, "status": "completed"}

    except Exception as e:
        return {**state, "status": "completed", "errors": state["errors"] + [f"Supabase (non bloquant) : {e}"]}


# ─── Graph ───────────────────────────────────────────────────────────────────
def build_graph():
    g = StateGraph(QuizState)

    g.add_node("generate_questions", generate_questions)
    g.add_node("evaluate_answers",   evaluate_answers)
    g.add_node("generate_feedback",  generate_feedback)
    g.add_node("save_session",       save_session)

    g.set_entry_point("generate_questions")

    g.add_conditional_edges("generate_questions", _stop_on_error("evaluate_answers"))
    g.add_conditional_edges("evaluate_answers",   _stop_on_error("generate_feedback"))
    g.add_conditional_edges("generate_feedback",  _stop_on_error("save_session"))
    g.add_edge("save_session", END)

    return g.compile()


def generate_quiz(learner_name: str, topic: str, current_level: str) -> QuizState:
    """Génère les questions du quiz."""
    initial_state = QuizState(
        learner_name  = learner_name,
        topic         = topic,
        current_level = current_level,
        questions     = None,
        answers       = None,
        score         = None,
        feedback      = None,
        next_level    = None,
        session_id    = None,
        errors        = [],
        status        = "pending",
    )
    g = StateGraph(QuizState)
    g.add_node("generate_questions", generate_questions)
    g.set_entry_point("generate_questions")
    g.add_edge("generate_questions", END)
    return g.compile().invoke(initial_state)


def evaluate_quiz(state: QuizState, answers: list) -> QuizState:
    """Évalue les réponses et génère le feedback."""
    state = {**state, "answers": answers}
    g = StateGraph(QuizState)
    g.add_node("evaluate_answers",  evaluate_answers)
    g.add_node("generate_feedback", generate_feedback)
    g.add_node("save_session",      save_session)
    g.set_entry_point("evaluate_answers")
    g.add_conditional_edges("evaluate_answers",  _stop_on_error("generate_feedback"))
    g.add_conditional_edges("generate_feedback", _stop_on_error("save_session"))
    g.add_edge("save_session", END)
    return g.compile().invoke(state)