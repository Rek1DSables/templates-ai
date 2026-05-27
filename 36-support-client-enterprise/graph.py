# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    SCORE_ESCALADE, SCORE_CONFIANCE_MIN
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class TicketState(TypedDict):
    ticket_id: str
    canal: str
    expediteur: str
    sujet: str
    message: str
    categorie: str
    priorite: str
    score_complexite: int
    reponse_kb: str
    reponse_redigee: str
    score_confiance: int
    decision: str
    justification: str
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 1000) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surcharge, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


# --- AGENT A : CLASSIFICATION ---
def agent_classification(state: TicketState) -> TicketState:
    try:
        system = """Tu es un agent de classification de tickets support. 
Tu analyses les tickets entrants et tu les classes precisement.
Tu reponds UNIQUEMENT en JSON valide sans backticks :
{
  "categorie": "technique|facturation|commercial|plainte|autre",
  "priorite": "critique|haute|normale|basse",
  "score_complexite": 1-10,
  "resume": "resume en une phrase du probleme"
}"""

        reponse = invoke_with_retry(
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Classifie ce ticket support :

Canal : {state['canal']}
Expediteur : {state['expediteur']}
Sujet : {state['sujet']}
Message : {state['message']}"""
            }],
        )

        import json
        data = json.loads(reponse.strip())

        return {
            **state,
            "categorie": data.get("categorie", "autre"),
            "priorite": data.get("priorite", "normale"),
            "score_complexite": int(data.get("score_complexite", 5)),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "categorie": "autre", "priorite": "normale", "score_complexite": 5, "erreur": f"Erreur classification : {str(e)}"}


# --- AGENT B : BASE DE CONNAISSANCE ---
def agent_knowledge_base(state: TicketState) -> TicketState:
    try:
        system = """Tu es un agent specialise dans la recherche de solutions support.
Tu as acces a une base de connaissance interne et tu trouves la reponse la plus pertinente.
Tu reponds toujours en francais avec une solution concrete et structuree."""

        kb_context = """BASE DE CONNAISSANCE INTERNE :

[TECHNIQUE] Reset mot de passe : Aller sur /reset-password, entrer son email, cliquer sur le lien recu.
[TECHNIQUE] Connexion impossible : Vider le cache, essayer un autre navigateur, verifier les identifiants.
[TECHNIQUE] Application lente : Verifier la connexion internet, redemarrer l'application, vider le cache.
[FACTURATION] Remboursement : Delai de 5-10 jours ouvrés, contacter facturation@entreprise.com.
[FACTURATION] Changement abonnement : Possible depuis l'espace client > Mon abonnement.
[COMMERCIAL] Demo produit : Disponible sur demande, prendre RDV sur calendly.com/demo.
[PLAINTE] Procedure : Accusé reception sous 24h, traitement sous 72h, escalade manager si non résolu."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Trouve la solution pour ce ticket :

Categorie : {state['categorie']}
Priorite : {state['priorite']}
Message client : {state['message']}

{kb_context}

Fournis la solution la plus adaptee depuis la base de connaissance."""
            }],
            max_tokens=800,
        )

        return {**state, "reponse_kb": reponse, "erreur": ""}
    except Exception as e:
        return {**state, "reponse_kb": "", "erreur": f"Erreur KB : {str(e)}"}


# --- AGENT C : REDACTION ---
def agent_redaction(state: TicketState) -> TicketState:
    try:
        system = """Tu es un agent de redaction specialise dans le support client professionnel.
Tu rediges des reponses claires, empathiques et actionnables.
Tu reponds toujours en francais avec un ton professionnel mais humain."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Redige une reponse professionnelle pour ce ticket :

Expediteur : {state['expediteur']}
Sujet : {state['sujet']}
Message original : {state['message']}
Categorie : {state['categorie']}
Priorite : {state['priorite']}
Solution identifiee : {state['reponse_kb']}

La reponse doit :
- Commencer par accueillir le client par son nom si disponible
- Accuser reception du probleme avec empathie
- Proposer la solution de facon claire et sequencee
- Terminer avec une formule de politesse et une invitation a recontacter
- Etre signee "L'equipe Support" """
            }],
            max_tokens=800,
        )

        return {**state, "reponse_redigee": reponse, "erreur": ""}
    except Exception as e:
        return {**state, "reponse_redigee": "", "erreur": f"Erreur redaction : {str(e)}"}


# --- AGENT D : VERIFICATION & DECISION ---
def agent_verification(state: TicketState) -> TicketState:
    try:
        system = """Tu es un agent de verification qualite support client.
Tu evalues la reponse redigee et tu decides de l'action finale.
Tu reponds UNIQUEMENT avec ce JSON exact, sans texte avant ou apres, sans backticks :
{"score_confiance": 8, "decision": "envoyer", "justification": "raison en une phrase"}

Les valeurs possibles pour decision sont uniquement : envoyer, escalader, revoir"""

        reponse = invoke_with_retry(
            system=system,
            messages=[{
                "role": "user",
                "content": f"""Evalue cette reponse support :

Ticket original : {state['message']}
Categorie : {state['categorie']}
Score complexite : {state['score_complexite']}/10
Reponse redigee : {state['reponse_redigee']}

Si score complexite >= 8 : decision = escalader
Si reponse claire et complete : decision = envoyer
Sinon : decision = revoir

Reponds uniquement avec le JSON."""
            }],
        )

        import json
        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)

        score_confiance = int(data.get("score_confiance", 5))
        decision = data.get("decision", "escalader")

        if state["score_complexite"] >= 8:
            decision = "escalader"

        return {
            **state,
            "score_confiance": score_confiance,
            "decision": decision,
            "justification": data.get("justification", ""),
            "erreur": "",
        }
    except Exception as e:
        # Fallback : on prend une decision basee sur le score de complexite
        decision = "escalader" if state["score_complexite"] >= 6 else "envoyer"
        return {
            **state,
            "score_confiance": 5,
            "decision": decision,
            "justification": f"Decision automatique (parsing JSON echoue : {str(e)})",
            "erreur": "",
        }

        import json
        data = json.loads(reponse.strip())

        score_confiance = int(data.get("score_confiance", 5))
        decision = data.get("decision", "escalader")

        if state["score_complexite"] >= 8:
            decision = "escalader"

        return {
            **state,
            "score_confiance": score_confiance,
            "decision": decision,
            "justification": data.get("justification", ""),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "score_confiance": 5, "decision": "escalader", "justification": str(e), "erreur": f"Erreur verification : {str(e)}"}


def router(state: TicketState) -> str:
    return state.get("decision", "escalader")


def build_graph():
    graph = StateGraph(TicketState)
    graph.add_node("agent_classification", agent_classification)
    graph.add_node("agent_knowledge_base", agent_knowledge_base)
    graph.add_node("agent_redaction", agent_redaction)
    graph.add_node("agent_verification", agent_verification)

    graph.set_entry_point("agent_classification")
    graph.add_edge("agent_classification", "agent_knowledge_base")
    graph.add_edge("agent_knowledge_base", "agent_redaction")
    graph.add_edge("agent_redaction", "agent_verification")
    graph.add_conditional_edges(
        "agent_verification",
        router,
        {
            "envoyer": END,
            "escalader": END,
            "revoir": END,
        }
    )

    return graph.compile()