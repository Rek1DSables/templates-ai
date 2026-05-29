# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    SEUIL_ECART_CRITIQUE, SEUIL_ECART_ELEVE
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class FinanceCloseState(TypedDict):
    entreprise: str
    type_cloture: str
    periode: str
    norme: str
    devise: str
    comptes: list
    transactions: list
    budget: dict
    reel: dict
    entites: list
    reconciliations: list
    variances: list
    journal_entries: list
    anomalies: list
    disclosure: str
    rapport_final: str
    score_qualite: int
    audit_log: list
    erreur: str


def invoke_with_retry(messages: list, system: str, max_tokens: int = 2000, model: str = None) -> str:
    m = model or MODEL_NAME
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=m,
                max_tokens=max_tokens,
                system=messages,
                messages=messages,
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surcharge, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def invoke_with_retry(messages: list, system: str, max_tokens: int = 2000, model: str = None) -> str:
    m = model or MODEL_NAME
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=m,
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


def log_action(audit_log: list, etape: str, agent: str, statut: str, detail: str = "") -> list:
    audit_log.append({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "etape": etape,
        "agent": agent,
        "statut": statut,
        "detail": detail,
    })
    return audit_log


def agent_reconciliation(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Réconciliation des comptes", "Agent Réconciliation", "en_cours")

        system = """Tu es un agent de reconciliation comptable expert.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "reconciliations": [
    {"compte": "411", "libelle": "Clients", "solde_gl": 285000, "solde_auxiliaire": 284200, "ecart": 800, "statut": "ecart_mineur", "action": "Verifier facture", "priorite": "normale"}
  ],
  "anomalies": [
    {"type": "Doublon", "compte": "401", "montant": 1500, "description": "Transaction doublee", "niveau": "critique"}
  ],
  "score_reconciliation": 85,
  "comptes_reconcilies": 7,
  "comptes_en_ecart": 2
}"""

        comptes_str = "\n".join([
            f"- {c.get('numero')} {c.get('libelle')} : GL={c.get('solde_gl')} | Aux={c.get('solde_auxiliaire')} {state['devise']}"
            for c in state["comptes"]
        ])

        prompt = f"""Reconciliation comptable :

Entreprise : {state['entreprise']} | Periode : {state['periode']}
Norme : {state['norme']} | Devise : {state['devise']}

COMPTES :
{comptes_str}

TRANSACTIONS :
{json.dumps(state['transactions'][:8], ensure_ascii=False)}

Identifies ecarts, doublons, anomalies. JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=1500)
        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        data = json.loads(reponse_clean.strip())

        audit_log = log_action(audit_log, "Réconciliation terminée", "Agent Réconciliation", "complete",
            f"{data.get('comptes_reconcilies')} comptes | {data.get('comptes_en_ecart')} ecarts | Score {data.get('score_reconciliation')}/100")

        return {**state, "reconciliations": data.get("reconciliations", []), "anomalies": data.get("anomalies", []), "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur reconciliation : {str(e)}"}


def agent_variance(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Analyse variances Budget vs Réel", "Agent Variance", "en_cours")

        system = """Tu es un agent d analyse financiere expert.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "variances": [
    {"poste": "Chiffre d affaires", "budget": 500000, "reel": 475000, "ecart_absolu": -25000, "ecart_pct": -5.0, "niveau": "critique", "cause_probable": "Retard livraison", "action_requise": "Analyser pipeline"}
  ],
  "score_performance": 72,
  "postes_favorables": 3,
  "postes_defavorables": 4,
  "alerte_globale": "Performance sous budget de 5% sur CA"
}"""

        prompt = f"""Analyse variances Budget vs Reel :

Entreprise : {state['entreprise']} | Periode : {state['periode']}
Seuil critique : {SEUIL_ECART_CRITIQUE}% | Seuil eleve : {SEUIL_ECART_ELEVE}%

BUDGET : {json.dumps(state['budget'], ensure_ascii=False)}
REEL : {json.dumps(state['reel'], ensure_ascii=False)}

Calcule ecarts absolus et pourcentages. JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=1500)
        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        data = json.loads(reponse_clean.strip())

        audit_log = log_action(audit_log, "Variances terminées", "Agent Variance", "complete",
            f"Score {data.get('score_performance')}/100 | {data.get('postes_defavorables')} postes defavorables")

        return {**state, "variances": data.get("variances", []), "score_qualite": data.get("score_performance", 50), "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur variance : {str(e)}"}


def agent_journal_entries(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Génération écritures de clôture", "Agent Journal Entries", "en_cours")

        system = """Tu es un expert comptable specialise en clotures.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "journal_entries": [
    {"reference": "JE-001", "date": "2026-05-31", "libelle": "Charge a payer loyer", "debit": {"compte": "613", "libelle": "Loyers", "montant": 5000}, "credit": {"compte": "408", "libelle": "FAB", "montant": 5000}, "type": "regularisation", "auto_reverse": true, "approuve": false, "priorite": "haute"}
  ],
  "total_entries": 3,
  "impact_resultat": -7500
}"""

        anomalies_str = json.dumps(state["anomalies"][:5], ensure_ascii=False)
        ecarts_str = json.dumps([r for r in state["reconciliations"] if r.get("ecart", 0) != 0][:5], ensure_ascii=False)

        prompt = f"""Genere les ecritures de cloture :

Entreprise : {state['entreprise']} | Periode : {state['periode']}
Norme : {state['norme']} | Devise : {state['devise']}

ANOMALIES : {anomalies_str}
ECARTS : {ecarts_str}

Ecritures equilibrees (debit = credit). JSON uniquement."""

        reponse = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=1500)
        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        data = json.loads(reponse_clean.strip())

        audit_log = log_action(audit_log, "Journal entries terminées", "Agent Journal Entries", "complete",
            f"{data.get('total_entries')} ecritures | Impact : {data.get('impact_resultat')} {state['devise']}")

        return {**state, "journal_entries": data.get("journal_entries", []), "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur journal entries : {str(e)}"}


def agent_disclosure_partie1(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Disclosure partie 1", "Agent Disclosure", "en_cours")

        system = """Tu es un expert en reporting financier.
Tu rediges en francais professionnel concis.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige UNIQUEMENT la section 1 du rapport de cloture :

{state['entreprise']} | {state['periode']} | Score {state['score_qualite']}/100
Variances critiques : {len([v for v in state['variances'] if v.get('niveau') == 'critique'])}
Anomalies : {len(state['anomalies'])}

SECTION 1 — SYNTHESE EXECUTIVE (max 200 mots)
- Statut cloture : Prete / Sous conditions / Bloquee
- 4 points cles de la periode
- Score qualite justifie
- 2 points attention direction

Termine le dernier point attention."""

        partie1 = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=600, model=MODEL_SONNET)
        audit_log = log_action(audit_log, "Disclosure partie 1 terminée", "Agent Disclosure", "complete")

        return {**state, "disclosure": partie1, "rapport_final": partie1, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur disclosure partie 1 : {str(e)}"}


def agent_disclosure_partie2(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Disclosure partie 2", "Agent Disclosure", "en_cours")

        system = """Tu es un expert en reporting financier.
Tu rediges en francais professionnel concis.
Tu termines TOUJOURS ta section avant de t'arreter."""

        variances_str = "\n".join([
            f"- {v.get('poste')} : {v.get('ecart_pct')}% | {v.get('cause_probable')}"
            for v in state["variances"] if v.get("niveau") in ["critique", "eleve"]
        ])

        prompt = f"""Redige UNIQUEMENT la section 2 du rapport de cloture :

{state['entreprise']} | {state['periode']}

VARIANCES SIGNIFICATIVES :
{variances_str if variances_str else 'Aucune variance critique'}

SECTION 2 — ANALYSE DES VARIANCES (max 200 mots)
Pour chaque variance critique :
- Explication en 1-2 lignes
- Impact financier chiffre
- Action corrective concrete

Termine la derniere action corrective."""

        partie2 = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=600, model=MODEL_SONNET)
        rapport = state["rapport_final"] + "\n\n" + partie2
        audit_log = log_action(audit_log, "Disclosure partie 2 terminée", "Agent Disclosure", "complete")

        return {**state, "disclosure": rapport, "rapport_final": rapport, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur disclosure partie 2 : {str(e)}"}


def agent_disclosure_partie3(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Disclosure partie 3", "Agent Disclosure", "en_cours")

        system = """Tu es un expert en reporting financier.
Tu rediges en francais professionnel concis.
Tu termines TOUJOURS ta section avant de t'arreter."""

        je_str = "\n".join([
            f"- {je.get('reference')} : {je.get('libelle')} | {je.get('debit', {}).get('montant', 0)} {state['devise']} | Auto-reverse : {je.get('auto_reverse')}"
            for je in state["journal_entries"][:5]
        ])

        prompt = f"""Redige UNIQUEMENT la section 3 du rapport de cloture :

{state['entreprise']} | {state['periode']} | Norme : {state['norme']}

ECRITURES GENEREES :
{je_str if je_str else 'Aucune ecriture'}

SECTION 3 — ECRITURES ET CHECKLIST (max 200 mots)

Ecritures generees :
- Resume en 3 lignes max
- Impact resultat global

Checklist cloture (8 points) :
[OK] ou [A FAIRE] — Point — Responsable
1. ...
2. ...
3. ...
4. ...
5. ...
6. ...
7. ...
8. ...

Termine le point 8."""

        partie3 = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=600, model=MODEL_SONNET)
        rapport = state["rapport_final"] + "\n\n" + partie3
        audit_log = log_action(audit_log, "Disclosure partie 3 terminée", "Agent Disclosure", "complete")

        return {**state, "disclosure": rapport, "rapport_final": rapport, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur disclosure partie 3 : {str(e)}"}


def agent_disclosure_partie4(state: FinanceCloseState) -> FinanceCloseState:
    try:
        audit_log = log_action(state.get("audit_log", []), "Disclosure partie 4 — Conclusion", "Agent Disclosure", "en_cours")

        system = """Tu es un expert en reporting financier.
Tu rediges en francais professionnel concis.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige UNIQUEMENT la conclusion du rapport de cloture :

{state['entreprise']} | {state['periode']} | Score {state['score_qualite']}/100 | Norme : {state['norme']}

SECTION 4 — CONCLUSION (max 150 mots)

STATUT FINAL : Prete / Sous conditions / Bloquee (1 phrase)

VALIDATION :
- Approbateur : [CFO / DAF / CAC]
- Delai : [date]
- Reference : {state['norme']}

PROCHAINE PERIODE — 3 actions :
1. [action]
2. [action]
3. [action]

Termine l action 3."""

        partie4 = invoke_with_retry(system=system, messages=[{"role": "user", "content": prompt}], max_tokens=400, model=MODEL_SONNET)
        rapport = state["rapport_final"] + "\n\n" + partie4

        audit_log = log_action(audit_log, "Clôture terminée", "system", "complete",
            f"Score {state['score_qualite']}/100 | {len(state['journal_entries'])} ecritures | {len(state['anomalies'])} anomalies")

        return {**state, "disclosure": rapport, "rapport_final": rapport, "audit_log": audit_log, "erreur": ""}
    except Exception as e:
        return {**state, "erreur": f"Erreur disclosure partie 4 : {str(e)}"}


def build_graph():
    graph = StateGraph(FinanceCloseState)
    graph.add_node("agent_reconciliation", agent_reconciliation)
    graph.add_node("agent_variance", agent_variance)
    graph.add_node("agent_journal_entries", agent_journal_entries)
    graph.add_node("agent_disclosure_partie1", agent_disclosure_partie1)
    graph.add_node("agent_disclosure_partie2", agent_disclosure_partie2)
    graph.add_node("agent_disclosure_partie3", agent_disclosure_partie3)
    graph.add_node("agent_disclosure_partie4", agent_disclosure_partie4)

    graph.set_entry_point("agent_reconciliation")
    graph.add_edge("agent_reconciliation", "agent_variance")
    graph.add_edge("agent_variance", "agent_journal_entries")
    graph.add_edge("agent_journal_entries", "agent_disclosure_partie1")
    graph.add_edge("agent_disclosure_partie1", "agent_disclosure_partie2")
    graph.add_edge("agent_disclosure_partie2", "agent_disclosure_partie3")
    graph.add_edge("agent_disclosure_partie3", "agent_disclosure_partie4")
    graph.add_edge("agent_disclosure_partie4", END)

    return graph.compile()