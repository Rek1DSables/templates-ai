# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class OnboardingState(TypedDict):
    prenom: str
    nom: str
    poste: str
    departement: str
    date_arrivee: str
    manager: str
    email_employe: str
    email_bienvenue: str
    checklist: str
    acces: str
    erreur: str


def invoke_with_retry(messages: list, system: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=2000,
                system=system,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surchargé, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def generer_email_bienvenue(state: OnboardingState) -> OnboardingState:
    try:
        system = (
            "Tu es un responsable RH bienveillant et professionnel. "
            "Tu rediges des emails de bienvenue chaleureux et motivants pour les nouveaux employes. "
            "Ton ton est professionnel mais humain. Tu utilises le prenom du nouvel employe."
        )
        prompt = f"""Redige un email de bienvenue pour un nouvel employe avec ces informations :

Prenom : {state['prenom']}
Nom : {state['nom']}
Poste : {state['poste']}
Departement : {state['departement']}
Date d'arrivee : {state['date_arrivee']}
Manager : {state['manager']}

L'email doit :
- Accueillir chaleureusement le nouvel employe
- Mentionner son poste et son departement
- Indiquer que son manager {state['manager']} sera present pour l'accueillir
- Donner 3 conseils pratiques pour bien demarrer
- Terminer sur une note enthousiaste
- Avoir un objet d'email professionnel en premiere ligne (format : Objet: ...)"""

        email = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "email_bienvenue": email, "erreur": ""}
    except Exception as e:
        return {**state, "email_bienvenue": "", "erreur": f"Erreur email : {str(e)}"}


def generer_checklist(state: OnboardingState) -> OnboardingState:
    try:
        system = (
            "Tu es un expert en processus RH. "
            "Tu generes des checklists d'onboarding claires, pratiques et exhaustives. "
            "Tu structures toujours par categories avec des cases a cocher."
        )
        prompt = f"""Genere une checklist d'onboarding complete pour :

Poste : {state['poste']}
Departement : {state['departement']}
Date d'arrivee : {state['date_arrivee']}

La checklist doit couvrir ces categories :
1. Avant l'arrivee (preparations RH)
2. Jour J (accueil physique)
3. Semaine 1 (integration)
4. Mois 1 (montee en competences)

Format : categories en majuscules, items avec [ ] devant chaque tache."""

        checklist = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "checklist": checklist, "erreur": ""}
    except Exception as e:
        return {**state, "checklist": "", "erreur": f"Erreur checklist : {str(e)}"}


def generer_acces(state: OnboardingState) -> OnboardingState:
    try:
        system = (
            "Tu es un responsable IT. "
            "Tu generes des listes d'acces et de provisionning pour les nouveaux employes. "
            "Tu es precis, technique et exhaustif."
        )
        prompt = f"""Genere la liste des acces et outils a provisionner pour :

Poste : {state['poste']}
Departement : {state['departement']}

La liste doit couvrir :
1. Comptes et acces (email, SSO, VPN...)
2. Outils metier (selon le poste et departement)
3. Acces physiques (badge, bureaux...)
4. Formations obligatoires (securite, RGPD...)

Format : categories en majuscules, items avec [ ] devant chaque element."""

        acces = invoke_with_retry(
            messages=[{"role": "user", "content": prompt}],
            system=system,
        )
        return {**state, "acces": acces, "erreur": ""}
    except Exception as e:
        return {**state, "acces": "", "erreur": f"Erreur acces : {str(e)}"}


def build_graph():
    graph = StateGraph(OnboardingState)
    graph.add_node("generer_email_bienvenue", generer_email_bienvenue)
    graph.add_node("generer_checklist", generer_checklist)
    graph.add_node("generer_acces", generer_acces)

    graph.set_entry_point("generer_email_bienvenue")
    graph.add_edge("generer_email_bienvenue", "generer_checklist")
    graph.add_edge("generer_checklist", "generer_acces")
    graph.add_edge("generer_acces", END)

    return graph.compile()