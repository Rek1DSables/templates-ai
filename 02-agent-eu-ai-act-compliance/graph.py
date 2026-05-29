# graph.py
import time
import json
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, MODEL_SONNET, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY, ARTICLES_EU_AI_ACT
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ComplianceState(TypedDict):
    nom_systeme: str
    description: str
    secteur: str
    categorie_risque: str
    usages: str
    donnees_traitees: str
    utilisateurs: str
    classification: dict
    analyse_articles: dict
    gaps: list
    plan_remediation: str
    score_conformite: int
    audit_trail: list
    erreur: str


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


def classifier_systeme(state: ComplianceState) -> ComplianceState:
    try:
        audit_trail = state.get("audit_trail", [])
        audit_trail.append({
            "etape": "Classification du système",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "classifier_systeme",
            "statut": "en_cours"
        })

        system = """Tu es un expert juridique specialise en EU AI Act et conformite reglementaire IA.
Tu classes les systemes IA selon le reglement EU 2024/1689.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "niveau_risque": "Eleve",
  "justification": "justification precise en 3-4 lignes",
  "articles_applicables": ["Article 6", "Article 9", "Article 13"],
  "categorie_annexe_iii": "categorie si applicable ou null",
  "est_gpai": false,
  "pratiques_interdites": false,
  "score_risque_initial": 65,
  "flags_critiques": ["flag 1", "flag 2"]
}"""

        prompt = f"""Classe ce systeme IA selon l EU AI Act :

NOM : {state['nom_systeme']}
DESCRIPTION : {state['description']}
SECTEUR : {state['secteur']}
CATEGORIE DECLAREE : {state['categorie_risque']}
USAGES : {state['usages']}
DONNEES TRAITEES : {state['donnees_traitees']}
UTILISATEURS : {state['utilisateurs']}

Determines le niveau de risque EU AI Act (Inacceptable / Eleve / Limite / Minimal).
Identifies les articles applicables et les flags critiques.
JSON uniquement."""

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

        classification = json.loads(reponse_clean)

        audit_trail[-1]["statut"] = "complete"
        audit_trail[-1]["resultat"] = f"Niveau risque : {classification.get('niveau_risque')} | Score : {classification.get('score_risque_initial')}/100"

        return {
            **state,
            "classification": classification,
            "audit_trail": audit_trail,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur classification : {str(e)}"}


def analyser_conformite_articles(state: ComplianceState) -> ComplianceState:
    try:
        audit_trail = state.get("audit_trail", [])
        analyse_par_article = {}

        system = """Tu es un expert EU AI Act. Tu analyses la conformite d un systeme IA par article.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks :
{
  "statut": "conforme|partiel|non_conforme|non_applicable",
  "score": 70,
  "constats": ["constat 1", "constat 2"],
  "gaps": ["gap 1", "gap 2"],
  "actions_requises": ["action 1", "action 2"],
  "deadline": "Aout 2026"
}"""

        articles_applicables = state["classification"].get("articles_applicables", list(ARTICLES_EU_AI_ACT.keys())[:5])

        for article, description in ARTICLES_EU_AI_ACT.items():
            if not any(art in article for art in [a.split(" — ")[0] for a in articles_applicables]):
                continue

            audit_trail.append({
                "etape": f"Analyse {article}",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "agent": "analyser_conformite_articles",
                "statut": "en_cours"
            })

            prompt = f"""Analyse la conformite de ce systeme IA pour {article} :

Description de l article : {description}

SYSTEME :
- Nom : {state['nom_systeme']}
- Description : {state['description']}
- Secteur : {state['secteur']}
- Usages : {state['usages']}
- Donnees : {state['donnees_traitees']}
- Niveau risque classe : {state['classification'].get('niveau_risque')}

Identifies les gaps de conformite et les actions requises.
JSON uniquement."""

            reponse = invoke_with_retry(
                system=system,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=800,
            )

            reponse_clean = reponse.strip()
            if reponse_clean.startswith("```"):
                reponse_clean = reponse_clean.split("```")[1]
                if reponse_clean.startswith("json"):
                    reponse_clean = reponse_clean[4:]
            reponse_clean = reponse_clean.strip()

            try:
                data = json.loads(reponse_clean)
            except Exception:
                data = {"statut": "non_conforme", "score": 0, "constats": [], "gaps": ["Analyse indisponible"], "actions_requises": [], "deadline": "Août 2026"}

            analyse_par_article[article] = data
            audit_trail[-1]["statut"] = "complete"
            audit_trail[-1]["resultat"] = f"Statut : {data.get('statut')} | Score : {data.get('score')}/100"

        gaps_globaux = []
        for article, data in analyse_par_article.items():
            for gap in data.get("gaps", []):
                gaps_globaux.append({"article": article, "gap": gap, "priorite": "haute" if data.get("statut") == "non_conforme" else "moyenne"})

        scores = [v.get("score", 50) for v in analyse_par_article.values() if v.get("statut") != "non_applicable"]
        score_global = int(sum(scores) / len(scores)) if scores else 0

        return {
            **state,
            "analyse_articles": analyse_par_article,
            "gaps": gaps_globaux,
            "score_conformite": score_global,
            "audit_trail": audit_trail,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur analyse articles : {str(e)}"}


def generer_plan_remediation_partie1(state: ComplianceState) -> ComplianceState:
    try:
        audit_trail = state.get("audit_trail", [])
        audit_trail.append({
            "etape": "Génération plan de remédiation — Partie 1",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "generer_plan_remediation_partie1",
            "statut": "en_cours"
        })

        system = """Tu es un consultant senior specialise EU AI Act.
Tu rediges des plans de remediation conformite en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        gaps_str = "\n".join([f"- [{g['priorite'].upper()}] {g['article']} : {g['gap']}" for g in state["gaps"][:8]])
        articles_str = "\n".join([
            f"- {art} : {data.get('statut')} ({data.get('score')}/100)"
            for art, data in state["analyse_articles"].items()
        ])

        prompt = f"""Redige la PARTIE 1 du plan de remediation EU AI Act :

SYSTEME : {state['nom_systeme']}
SECTEUR : {state['secteur']}
NIVEAU RISQUE : {state['classification'].get('niveau_risque')}
SCORE CONFORMITE : {state['score_conformite']}/100

ANALYSE PAR ARTICLE :
{articles_str}

GAPS IDENTIFIES :
{gaps_str}

Redige ces 2 sections :

1. SYNTHESE EXECUTIVE
   - Verdict de conformite (conforme / partiellement conforme / non conforme)
   - 5 constats cles
   - Risques reglementaires principaux (amendes potentielles, interdictions)
   - Deadlines critiques a respecter

2. GAPS PRIORITAIRES PAR ARTICLE
   - Pour chaque article non conforme : gap precise + impact + urgence
   - Code couleur : CRITIQUE / ELEVE / MOYEN

Termine imperativement la section 2."""

        plan_partie1 = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            model=MODEL_SONNET,
        )

        audit_trail[-1]["statut"] = "complete"

        return {
            **state,
            "plan_remediation": plan_partie1,
            "audit_trail": audit_trail,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur plan partie 1 : {str(e)}"}


def generer_plan_remediation_partie2(state: ComplianceState) -> ComplianceState:
    try:
        audit_trail = state.get("audit_trail", [])
        audit_trail.append({
            "etape": "Génération plan de remédiation — Partie 2",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "generer_plan_remediation_partie2",
            "statut": "en_cours"
        })

        system = """Tu es un consultant senior specialise EU AI Act.
Tu rediges des plans de remediation conformite en francais professionnel.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige la PARTIE 2 du plan de remediation EU AI Act :

SYSTEME : {state['nom_systeme']}
NIVEAU RISQUE : {state['classification'].get('niveau_risque')}
SCORE CONFORMITE : {state['score_conformite']}/100
DEADLINE CRITIQUE : Aout 2026

Redige ces 2 sections :

3. PLAN D'ACTION 90 JOURS
   Pour chaque action :
   - Titre de l action
   - Priorite : CRITIQUE / ELEVE / MOYEN
   - Responsable recommande (DPO / RSSI / CTO / Direction juridique)
   - Delai : J+15 / J+30 / J+60 / J+90
   - Livrable attendu
   - Article EU AI Act adresse

   Minimum 8 actions concretes couvrant tous les gaps identifies.

4. CHECKLIST DE CONFORMITE
   Liste de verification en 15 points :
   [ ] Point 1 — article concerne
   [ ] Point 2 — ...
   etc.

Termine imperativement la checklist."""

        plan_partie2 = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            model=MODEL_SONNET,
        )

        plan_complet = state["plan_remediation"] + "\n\n" + plan_partie2
        audit_trail[-1]["statut"] = "complete"

        return {
            **state,
            "plan_remediation": plan_complet,
            "audit_trail": audit_trail,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur plan partie 2 : {str(e)}"}


def generer_verdict_final(state: ComplianceState) -> ComplianceState:
    try:
        audit_trail = state.get("audit_trail", [])
        audit_trail.append({
            "etape": "Verdict final et recommandations",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "generer_verdict_final",
            "statut": "en_cours"
        })

        system = """Tu es un consultant senior specialise EU AI Act.
Tu rediges en francais professionnel et concis.
Tu termines TOUJOURS ta section avant de t'arreter."""

        prompt = f"""Redige UNIQUEMENT le VERDICT FINAL de cet audit EU AI Act :

SYSTEME : {state['nom_systeme']}
NIVEAU RISQUE : {state['classification'].get('niveau_risque')}
SCORE CONFORMITE : {state['score_conformite']}/100
FLAGS CRITIQUES : {', '.join(state['classification'].get('flags_critiques', []))}

Structure courte et obligatoire :

VERDICT : Conforme / Partiellement conforme / Non conforme (1 phrase + 2 lignes)

RISQUE REGLEMENTAIRE :
- Amende potentielle maximale (selon niveau risque EU AI Act)
- Risque d interdiction de deploiement
- Risque reputationnel

3 ACTIONS IMMEDIATES (a faire avant tout) :
1. [action] | [responsable] | [delai]
2. [action] | [responsable] | [delai]
3. [action] | [responsable] | [delai]

PROCHAINE ETAPE RECOMMANDEE :
- 1 phrase concrete sur ce que le client doit faire maintenant

Termine la prochaine etape."""

        verdict = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            model=MODEL_SONNET,
        )

        plan_final = state["plan_remediation"] + "\n\n" + verdict
        audit_trail[-1]["statut"] = "complete"
        audit_trail.append({
            "etape": "Audit terminé",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "agent": "system",
            "statut": "complete",
            "resultat": f"Score final : {state['score_conformite']}/100 | {len(state['gaps'])} gaps identifies"
        })

        return {
            **state,
            "plan_remediation": plan_final,
            "audit_trail": audit_trail,
            "erreur": "",
        }
    except Exception as e:
        return {**state, "erreur": f"Erreur verdict final : {str(e)}"}


def build_graph():
    graph = StateGraph(ComplianceState)
    graph.add_node("classifier_systeme", classifier_systeme)
    graph.add_node("analyser_conformite_articles", analyser_conformite_articles)
    graph.add_node("generer_plan_remediation_partie1", generer_plan_remediation_partie1)
    graph.add_node("generer_plan_remediation_partie2", generer_plan_remediation_partie2)
    graph.add_node("generer_verdict_final", generer_verdict_final)

    graph.set_entry_point("classifier_systeme")
    graph.add_edge("classifier_systeme", "analyser_conformite_articles")
    graph.add_edge("analyser_conformite_articles", "generer_plan_remediation_partie1")
    graph.add_edge("generer_plan_remediation_partie1", "generer_plan_remediation_partie2")
    graph.add_edge("generer_plan_remediation_partie2", "generer_verdict_final")
    graph.add_edge("generer_verdict_final", END)

    return graph.compile()