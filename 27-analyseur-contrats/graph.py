# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ContratAnalyseState(TypedDict):
    type_contrat: str
    contenu_texte: str
    clauses_extraites: str
    risques: str
    resume_executif: str
    recommandations: str
    score_risque: int
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


def extraire_clauses(state: ContratAnalyseState) -> ContratAnalyseState:
    try:
        system = """Tu es un juriste expert en droit des contrats francais.
Tu analyses des contrats et extrais les clauses importantes avec precision.
Tu reponds toujours en francais avec un style juridique clair."""

        prompt = f"""Analyse ce contrat de type "{state['type_contrat']}" et extrait les clauses importantes :

CONTENU DU CONTRAT :
{state['contenu_texte'][:4000]}

Extrait et structure les clauses suivantes (si presentes) :

1. PARTIES : identification des parties (nom, statut, coordonnees)
2. OBJET : description precise de la prestation ou de l'accord
3. DUREE : date de debut, fin, reconduction tacite
4. PRIX ET PAIEMENT : montants, echeances, conditions de paiement
5. OBLIGATIONS : obligations de chaque partie
6. PROPRIETE INTELLECTUELLE : qui possede quoi
7. CONFIDENTIALITE : perimetre et duree
8. RESPONSABILITE : limitations, garanties
9. RESILIATION : conditions et preavis
10. LITIGES : juridiction competente, droit applicable

Pour chaque clause trouvee, indique le texte exact extrait du contrat."""

        clauses = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )
        return {**state, "clauses_extraites": clauses, "erreur": ""}
    except Exception as e:
        return {**state, "clauses_extraites": "", "erreur": f"Erreur extraction : {str(e)}"}


def analyser_risques(state: ContratAnalyseState) -> ContratAnalyseState:
    try:
        system = """Tu es un avocat specialise en droit des affaires et protection des interets des prestataires.
Tu identifies les clauses abusives, desequilibrees ou dangereuses dans les contrats.
Tu reponds toujours en francais."""

        prompt = f"""Analyse les risques de ce contrat :

Type : {state['type_contrat']}

CLAUSES EXTRAITES :
{state['clauses_extraites']}

CONTENU ORIGINAL :
{state['contenu_texte'][:2000]}

Identifie tous les risques et anomalies :

Pour chaque risque, indique :
- NIVEAU : critique / eleve / moyen / faible
- CLAUSE CONCERNEE : quelle clause pose probleme
- PROBLEME : description precise du risque
- IMPACT POTENTIEL : consequences si ce risque se materialise
- RECOMMANDATION : comment se proteger ou negocier

Exemples de risques a chercher :
- Clauses de responsabilite illimitee
- Absence de limitation de responsabilite
- Propriete intellectuelle cedee sans compensation
- Clause de non-concurrence excessive
- Paiements trop tardifs ou conditions floues
- Resiliation sans preavis ou abusive
- Juridiction defavorable
- Reconduction tacite sans information
- Obligations desequilibrees"""

        risques = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        # Score de risque basé sur le contenu
        score = 50
        if "critique" in risques.lower():
            score = min(score + 30, 100)
        if "eleve" in risques.lower():
            score = min(score + 20, 100)
        if "moyen" in risques.lower():
            score = min(score + 10, 100)

        return {**state, "risques": risques, "score_risque": score, "erreur": ""}
    except Exception as e:
        return {**state, "risques": "", "score_risque": 50, "erreur": f"Erreur risques : {str(e)}"}


def generer_resume(state: ContratAnalyseState) -> ContratAnalyseState:
    try:
        system = """Tu es un juriste senior expert en conseil contractuel.
Tu rediges des resumes executifs clairs et des recommandations actionnables.
Tu reponds toujours en francais avec un style professionnel."""

        prompt = f"""Redige un resume executif et des recommandations pour ce contrat :

Type : {state['type_contrat']}
Score de risque : {state['score_risque']}/100

CLAUSES EXTRAITES :
{state['clauses_extraites']}

RISQUES IDENTIFIES :
{state['risques']}

Redige :

1. RESUME EXECUTIF (5-7 points cles)
   - Nature et objet du contrat
   - Points favorables
   - Points defavorables
   - Verdict global (favorable / a negocier / risque eleve)

2. RECOMMANDATIONS PRIORITAIRES
   - Actions AVANT signature (points a negocier absolument)
   - Clauses a ajouter ou modifier
   - Points de vigilance a surveiller

3. VERDICT FINAL
   - Peut-on signer tel quel ?
   - Si non, quelles sont les conditions minimales ?"""

        resume = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        # Extraire recommandations
        recommandations = ""
        if "RECOMMANDATIONS" in resume:
            parts = resume.split("RECOMMANDATIONS")
            if len(parts) > 1:
                recommandations = parts[1].split("VERDICT")[0] if "VERDICT" in parts[1] else parts[1]

        return {**state, "resume_executif": resume, "recommandations": recommandations, "erreur": ""}
    except Exception as e:
        return {**state, "resume_executif": "", "recommandations": "", "erreur": f"Erreur resume : {str(e)}"}


def build_graph():
    graph = StateGraph(ContratAnalyseState)
    graph.add_node("extraire_clauses", extraire_clauses)
    graph.add_node("analyser_risques", analyser_risques)
    graph.add_node("generer_resume", generer_resume)

    graph.set_entry_point("extraire_clauses")
    graph.add_edge("extraire_clauses", "analyser_risques")
    graph.add_edge("analyser_risques", "generer_resume")
    graph.add_edge("generer_resume", END)

    return graph.compile()