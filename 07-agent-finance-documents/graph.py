# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class FinanceState(TypedDict):
    mode: str
    type_document: str
    contenu_document: str
    donnees_extraites: dict
    anomalies: list
    document_genere: str
    montant_ht: float
    montant_ttc: float
    taux_tva: float
    client_info: dict
    prestataire_info: dict
    lignes: list
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


def extraire_donnees(state: FinanceState) -> FinanceState:
    try:
        system = """Tu es un expert comptable et analyste financier.
Tu extrais les donnees structurees des documents financiers avec precision.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "type_document": "Facture",
  "numero": "FAC-2025-001",
  "date": "2025-06-01",
  "echeance": "2025-07-01",
  "emetteur": {"nom": "", "siret": "", "adresse": "", "email": ""},
  "destinataire": {"nom": "", "siret": "", "adresse": "", "email": ""},
  "lignes": [{"description": "", "quantite": 1, "prix_unitaire": 0.0, "tva": 20.0}],
  "montant_ht": 0.0,
  "montant_tva": 0.0,
  "montant_ttc": 0.0,
  "conditions_paiement": "",
  "statut_paiement": "En attente"
}"""

        prompt = f"""Extrait toutes les donnees de ce document financier :

Type attendu : {state['type_document']}

CONTENU :
{state['contenu_document'][:4000]}

Reponds uniquement avec le JSON."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )

        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)
        return {
            **state,
            "donnees_extraites": data,
            "montant_ht": float(data.get("montant_ht", 0)),
            "montant_ttc": float(data.get("montant_ttc", 0)),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "donnees_extraites": {}, "erreur": f"Erreur extraction : {str(e)}"}


def analyser_anomalies(state: FinanceState) -> FinanceState:
    try:
        system = """Tu es un expert comptable specialise dans la detection de fraudes et anomalies.
Tu analyses les documents financiers et identifies les irregularites.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "anomalies": [
    {
      "type": "Erreur de calcul",
      "niveau": "critique",
      "description": "description precise",
      "recommandation": "action a prendre"
    }
  ],
  "score_conformite": 85,
  "resume": "resume de l analyse"
}"""

        donnees_str = json.dumps(state["donnees_extraites"], ensure_ascii=False, indent=2)

        prompt = f"""Analyse ce document financier et detecte les anomalies :

Type : {state['type_document']}
Donnees extraites :
{donnees_str}

Verifie :
1. Coherence des calculs (HT + TVA = TTC)
2. Presence des mentions obligatoires (SIRET, numero, date)
3. Conformite des taux de TVA
4. Delais de paiement legaux (max 60 jours)
5. Anomalies de montants

Reponds uniquement avec le JSON."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )

        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)
        return {
            **state,
            "anomalies": data.get("anomalies", []),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "anomalies": [], "erreur": f"Erreur anomalies : {str(e)}"}


def generer_document(state: FinanceState) -> FinanceState:
    try:
        system = """Tu es un expert comptable qui redige des documents financiers professionnels.
Tu generes des documents conformes au droit francais.
Tu reponds toujours en francais avec un style professionnel."""

        lignes_str = "\n".join([
            f"- {l.get('description', '')} : {l.get('quantite', 1)} x {l.get('prix_unitaire', 0)}€ HT (TVA {l.get('tva', 20)}%)"
            for l in state["lignes"]
        ])

        client_info = state["client_info"]
        prestataire_info = state["prestataire_info"]
        montant_ht = state["montant_ht"]
        montant_ttc = montant_ht * (1 + state["taux_tva"] / 100)

        prompt = f"""Genere un {state['type_document']} professionnel et complet :

EMETTEUR :
- Nom : {prestataire_info.get('nom', '')}
- SIRET : {prestataire_info.get('siret', '')}
- Adresse : {prestataire_info.get('adresse', '')}
- Email : {prestataire_info.get('email', '')}

DESTINATAIRE :
- Nom : {client_info.get('nom', '')}
- Adresse : {client_info.get('adresse', '')}
- Email : {client_info.get('email', '')}

PRESTATIONS :
{lignes_str}

MONTANTS :
- Total HT : {montant_ht:.2f} EUR
- TVA ({state['taux_tva']}%) : {montant_ht * state['taux_tva'] / 100:.2f} EUR
- Total TTC : {montant_ttc:.2f} EUR

Genere le document complet avec toutes les mentions legales obligatoires."""

        document = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        return {
            **state,
            "document_genere": document,
            "montant_ttc": montant_ttc,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "document_genere": "", "erreur": f"Erreur generation : {str(e)}"}


def noeud_router(state: FinanceState) -> FinanceState:
    return state


def router(state: FinanceState) -> str:
    mode = state.get("mode", "")
    if "Analyser" in mode:
        return "vers_analyse"
    return "vers_generation"


def build_graph():
    graph = StateGraph(FinanceState)
    graph.add_node("noeud_router", noeud_router)
    graph.add_node("extraire_donnees", extraire_donnees)
    graph.add_node("analyser_anomalies", analyser_anomalies)
    graph.add_node("generer_document", generer_document)

    graph.set_entry_point("noeud_router")

    graph.add_conditional_edges(
        "noeud_router",
        router,
        {
            "vers_analyse": "extraire_donnees",
            "vers_generation": "generer_document",
        }
    )

    graph.add_edge("extraire_donnees", "analyser_anomalies")
    graph.add_edge("analyser_anomalies", END)
    graph.add_edge("generer_document", END)

    return graph.compile()