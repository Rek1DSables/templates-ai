# graph.py
import time
import json
import requests
from bs4 import BeautifulSoup
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
    HTTP_HEADERS, SCRAPING_TIMEOUT
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ScrapingState(TypedDict):
    mode: str
    urls: list
    texte_brut: str
    type_extraction: str
    champs_personnalises: list
    contenu_scrape: dict
    donnees_extraites: list
    nb_resultats: int
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


def scraper_url(url: str) -> str:
    try:
        response = requests.get(url, headers=HTTP_HEADERS, timeout=SCRAPING_TIMEOUT)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        texte = soup.get_text(separator="\n", strip=True)
        return texte[:6000]
    except Exception as e:
        return f"Erreur scraping {url} : {str(e)}"


def collecter_contenu(state: ScrapingState) -> ScrapingState:
    try:
        contenu = {}

        if state["mode"] == "Extraire depuis du texte brut":
            contenu["texte_brut"] = state["texte_brut"][:6000]

        elif state["mode"] == "Extraire depuis une URL":
            url = state["urls"][0] if state["urls"] else ""
            if url:
                contenu[url] = scraper_url(url)

        elif state["mode"] == "Extraire depuis une liste d'URLs":
            for url in state["urls"][:5]:
                contenu[url] = scraper_url(url)
                time.sleep(1)

        return {**state, "contenu_scrape": contenu, "erreur": ""}
    except Exception as e:
        return {**state, "contenu_scrape": {}, "erreur": f"Erreur collecte : {str(e)}"}


def extraire_donnees(state: ScrapingState) -> ScrapingState:
    try:
        tous_resultats = []

        if "Contacts" in state["type_extraction"]:
            schema = '{"nom": "", "email": "", "telephone": "", "entreprise": "", "poste": ""}'
        elif "Produits" in state["type_extraction"]:
            schema = '{"nom": "", "prix": "", "description": "", "disponibilite": ""}'
        elif "Offres" in state["type_extraction"]:
            schema = '{"titre": "", "entreprise": "", "lieu": "", "salaire": ""}'
        elif "Actualités" in state["type_extraction"]:
            schema = '{"titre": "", "date": "", "resume": "", "source": ""}'
        elif "Avis" in state["type_extraction"]:
            schema = '{"note": "", "auteur": "", "date": "", "commentaire": ""}'
        else:
            champs = state.get("champs_personnalises", [])
            schema = "{" + ", ".join([f'"{c}": ""' for c in champs]) + "}"

        system = f"""Tu es un expert en extraction de donnees structurees.
Tu extrais des informations depuis du contenu web.
Tu reponds UNIQUEMENT avec un JSON valide sans backticks.
IMPORTANT : maximum 5 resultats. JSON compact sans retours a la ligne inutiles.
Format strict : {{"resultats": [{schema}, ...]}}
Si aucune donnee : {{"resultats": []}}"""

        for source, contenu in state["contenu_scrape"].items():
            if not contenu or "Erreur" in str(contenu):
                continue

            prompt = f"""Extrait maximum 5 elements de type "{state['type_extraction']}" :

CONTENU :
{str(contenu)[:2000]}

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

            # Tenter de reparer le JSON si tronque
            try:
                data = json.loads(reponse_clean)
            except json.JSONDecodeError:
                # Chercher le dernier objet complet
                dernier_crochet = reponse_clean.rfind("]")
                if dernier_crochet > 0:
                    tente = reponse_clean[:dernier_crochet + 1] + "}"
                    try:
                        data = json.loads(tente)
                    except Exception:
                        continue
                else:
                    continue

            resultats = data.get("resultats", [])
            for r in resultats:
                r["_source"] = source
            tous_resultats.extend(resultats)

        return {
            **state,
            "donnees_extraites": tous_resultats,
            "nb_resultats": len(tous_resultats),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "donnees_extraites": [], "nb_resultats": 0, "erreur": f"Erreur extraction : {str(e)}"}

def build_graph():
    graph = StateGraph(ScrapingState)
    graph.add_node("collecter_contenu", collecter_contenu)
    graph.add_node("extraire_donnees", extraire_donnees)

    graph.set_entry_point("collecter_contenu")
    graph.add_edge("collecter_contenu", "extraire_donnees")
    graph.add_edge("extraire_donnees", END)

    return graph.compile()