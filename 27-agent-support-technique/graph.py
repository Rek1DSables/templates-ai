# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class SupportState(TypedDict):
    technologie: str
    type_probleme: str
    urgence: str
    description: str
    logs: str
    code: str
    diagnostic: str
    solutions: str
    plan_resolution: str
    prevention: str
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 2000) -> str:
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


def diagnostiquer_probleme(state: SupportState) -> SupportState:
    try:
        system = """Tu es un expert en debugging et support technique senior.
Tu analyses les problemes techniques avec precision et methode.
Tu reponds toujours en francais avec un style technique et clair."""

        prompt = f"""Analyse ce probleme technique :

Technologie : {state['technologie']}
Type : {state['type_probleme']}
Urgence : {state['urgence']}

Description du probleme :
{state['description']}

Logs / Messages d'erreur :
{state['logs'] if state['logs'] else "Aucun log fourni"}

Code concerne :
{state['code'] if state['code'] else "Aucun code fourni"}

Fournis un diagnostic structure :
1. CAUSE PROBABLE : identification precise de la cause racine
2. FACTEURS AGGRAVANTS : ce qui empire le probleme
3. IMPACT : evaluation de l'impact technique et business
4. NIVEAU DE COMPLEXITE : simple / moyen / complexe
5. TEMPS DE RESOLUTION ESTIME : estimation realiste"""

        diagnostic = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )
        return {**state, "diagnostic": diagnostic, "erreur": ""}
    except Exception as e:
        return {**state, "diagnostic": "", "erreur": f"Erreur diagnostic : {str(e)}"}


def generer_solutions(state: SupportState) -> SupportState:
    try:
        system = """Tu es un expert technique senior specialise en resolution de problemes.
Tu proposes des solutions concretes, testees et documentees.
Tu reponds toujours en francais avec du code quand c'est pertinent."""

        prompt = f"""Genere des solutions pour ce probleme :

Technologie : {state['technologie']}
Type : {state['type_probleme']}
Urgence : {state['urgence']}

Probleme :
{state['description']}

Logs :
{state['logs'] if state['logs'] else "Non fourni"}

Code :
{state['code'] if state['code'] else "Non fourni"}

Diagnostic :
{state['diagnostic']}

Propose 3 solutions dans l'ordre de priorite :

SOLUTION 1 — FIX IMMEDIAT (quick win) :
- Description de la solution
- Code ou commandes exactes
- Temps d'implementation : X minutes

SOLUTION 2 — SOLUTION COMPLETE :
- Description de la solution robuste
- Code ou commandes exactes
- Temps d'implementation : X heures

SOLUTION 3 — SOLUTION ALTERNATIVE :
- Approche differente si les precedentes echouent
- Code ou commandes exactes
- Temps d'implementation : X"""

        solutions = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return {**state, "solutions": solutions, "erreur": ""}
    except Exception as e:
        return {**state, "solutions": "", "erreur": f"Erreur solutions : {str(e)}"}


def generer_plan_resolution(state: SupportState) -> SupportState:
    try:
        system = """Tu es un lead technique expert en gestion d'incidents.
Tu rediges des plans de resolution clairs, step-by-step et actionnables.
Tu reponds toujours en francais."""

        prompt = f"""Redige un plan de resolution complet pour :

Technologie : {state['technologie']}
Urgence : {state['urgence']}

Diagnostic :
{state['diagnostic']}

Solutions disponibles :
{state['solutions']}

Le plan doit inclure :

PLAN DE RESOLUTION ETAPE PAR ETAPE :
Etape 1 : [Action immediate - < 5 min]
Etape 2 : [Diagnostic confirme - < 15 min]
Etape 3 : [Application du fix - < X min]
Etape 4 : [Verification et tests - < X min]
Etape 5 : [Documentation et post-mortem]

CHECKLIST DE VERIFICATION :
[ ] Verification 1
[ ] Verification 2
[ ] Verification 3

PREVENTION FUTURE :
- Bonne pratique 1
- Bonne pratique 2
- Monitoring recommande
- Tests a ajouter"""

        plan = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        # Extraire la section prevention
        prevention = ""
        if "PREVENTION" in plan:
            prevention = plan.split("PREVENTION")[1] if "PREVENTION" in plan else ""

        return {**state, "plan_resolution": plan, "prevention": prevention, "erreur": ""}
    except Exception as e:
        return {**state, "plan_resolution": "", "prevention": "", "erreur": f"Erreur plan : {str(e)}"}


def build_graph():
    graph = StateGraph(SupportState)
    graph.add_node("diagnostiquer_probleme", diagnostiquer_probleme)
    graph.add_node("generer_solutions", generer_solutions)
    graph.add_node("generer_plan_resolution", generer_plan_resolution)

    graph.set_entry_point("diagnostiquer_probleme")
    graph.add_edge("diagnostiquer_probleme", "generer_solutions")
    graph.add_edge("generer_solutions", "generer_plan_resolution")
    graph.add_edge("generer_plan_resolution", END)

    return graph.compile()