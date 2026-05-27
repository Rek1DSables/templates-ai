# graph.py
import time
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    SERPER_API_KEY, SERPER_URL,
    MAX_RETRIES, RETRY_DELAY
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class SEOState(TypedDict):
    url: str
    mots_cles: list
    type_site: str
    secteur: str
    contenu_page: str
    analyse_technique: str
    analyse_mots_cles: str
    analyse_concurrence: str
    rapport_seo: str
    score_seo: int
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


def recherche_serper(query: str, num: int = 5) -> list:
    try:
        headers = {"X-API-KEY": SERPER_API_KEY, "Content-Type": "application/json"}
        payload = {"q": query, "num": num}
        response = requests.post(SERPER_URL, headers=headers, json=payload, timeout=10)
        data = response.json()
        return data.get("organic", [])[:num]
    except Exception as e:
        return []


def scraper_page(url: str) -> dict:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")

        title = soup.find("title")
        meta_desc = soup.find("meta", attrs={"name": "description"})
        h1_tags = soup.find_all("h1")
        h2_tags = soup.find_all("h2")
        h3_tags = soup.find_all("h3")
        images = soup.find_all("img")
        links = soup.find_all("a", href=True)
        texte = soup.get_text(separator=" ", strip=True)[:3000]

        images_sans_alt = [img for img in images if not img.get("alt")]

        return {
            "title": title.get_text().strip() if title else "Manquant",
            "meta_description": meta_desc.get("content", "Manquante") if meta_desc else "Manquante",
            "h1": [h.get_text().strip() for h in h1_tags],
            "h2": [h.get_text().strip() for h in h2_tags[:5]],
            "h3": [h.get_text().strip() for h in h3_tags[:5]],
            "nb_images": len(images),
            "images_sans_alt": len(images_sans_alt),
            "nb_liens": len(links),
            "longueur_title": len(title.get_text().strip()) if title else 0,
            "longueur_meta": len(meta_desc.get("content", "")) if meta_desc else 0,
            "texte_extrait": texte,
            "status_code": response.status_code,
        }
    except Exception as e:
        return {"erreur": str(e)}


def analyser_technique(state: SEOState) -> SEOState:
    try:
        donnees = scraper_page(state["url"])

        if "erreur" in donnees:
            return {**state, "analyse_technique": f"Erreur scraping : {donnees['erreur']}", "contenu_page": "", "erreur": ""}

        system = """Tu es un expert SEO technique.
Tu analyses les elements techniques d'une page web et identifies les problemes SEO.
Tu reponds toujours en francais avec des recommandations concretes."""

        prompt = f"""Analyse technique SEO de cette page :

URL : {state['url']}
Type de site : {state['type_site']}
Secteur : {state['secteur']}

DONNEES TECHNIQUES :
- Title : "{donnees['title']}" ({donnees['longueur_title']} caracteres)
- Meta description : "{donnees['meta_description']}" ({donnees['longueur_meta']} caracteres)
- H1 : {donnees['h1']}
- H2 (premiers) : {donnees['h2']}
- H3 (premiers) : {donnees['h3']}
- Nombre d'images : {donnees['nb_images']} dont {donnees['images_sans_alt']} sans attribut alt
- Nombre de liens : {donnees['nb_liens']}
- Status HTTP : {donnees['status_code']}

EXTRAIT DU CONTENU :
{donnees['texte_extrait'][:1000]}

Analyse et note de 0 a 100 :
1. TITLE TAG : longueur, pertinence, mots-cles
2. META DESCRIPTION : longueur, attractivite
3. STRUCTURE H1/H2/H3 : hierarchie, pertinence
4. IMAGES : optimisation alt tags
5. CONTENU : densite, qualite, longueur estimee
6. SCORE TECHNIQUE GLOBAL : X/100

Fournis des recommandations specifiques pour chaque point."""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        return {
            **state,
            "analyse_technique": analyse,
            "contenu_page": donnees["texte_extrait"],
            "erreur": "",
        }
    except Exception as e:
        return {**state, "analyse_technique": "", "erreur": f"Erreur technique : {str(e)}"}


def analyser_mots_cles(state: SEOState) -> SEOState:
    try:
        resultats_par_mc = {}
        for mc in state["mots_cles"][:5]:
            resultats = recherche_serper(mc, num=5)
            resultats_par_mc[mc] = [
                {"position": i+1, "titre": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
                for i, r in enumerate(resultats)
            ]

        system = """Tu es un expert en analyse de mots-cles SEO.
Tu analyses le positionnement et la concurrence pour chaque mot-cle.
Tu reponds toujours en francais."""

        resultats_str = json.dumps(resultats_par_mc, ensure_ascii=False, indent=2)

        prompt = f"""Analyse ces mots-cles pour le site {state['url']} :

Mots-cles cibles : {', '.join(state['mots_cles'])}
Secteur : {state['secteur']}

RESULTATS SERP ACTUELS :
{resultats_str}

Pour chaque mot-cle, analyse :
1. DIFFICULTE : estimation de la difficulte a se positionner (faible/moyenne/elevee)
2. INTENTION : informationnelle, commerciale, transactionnelle ou navigationnelle
3. CONCURRENCE : qui domine les SERP et pourquoi
4. OPPORTUNITE : le site peut-il se positionner ? Dans quel delai ?
5. RECOMMANDATION : action prioritaire pour ce mot-cle"""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
        )

        return {**state, "analyse_mots_cles": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "analyse_mots_cles": "", "erreur": f"Erreur mots-cles : {str(e)}"}


def analyser_concurrence(state: SEOState) -> SEOState:
    try:
        query_conc = f"{state['secteur']} {state['mots_cles'][0] if state['mots_cles'] else ''} site concurrent"
        concurrents = recherche_serper(query_conc, num=5)

        domain = urlparse(state["url"]).netloc

        system = """Tu es un expert en analyse concurrentielle SEO.
Tu analyses les concurrents et identifies les opportunites de differentiation.
Tu reponds toujours en francais."""

        concurrents_str = "\n".join([
            f"- {c.get('title', '')} ({c.get('link', '')}) : {c.get('snippet', '')}"
            for c in concurrents
        ])

        prompt = f"""Analyse concurrentielle SEO pour :

Site analyse : {state['url']} ({domain})
Secteur : {state['secteur']}
Mots-cles cibles : {', '.join(state['mots_cles'])}

CONCURRENTS IDENTIFIES :
{concurrents_str}

Analyse :
1. POSITIONNEMENT CONCURRENTS : qui sont les leaders et pourquoi
2. POINTS FORTS CONCURRENTS : ce qu'ils font bien en SEO
3. FAILLES IDENTIFIEES : opportunites non exploitees par la concurrence
4. STRATEGIE DE DIFFERENCIATION : comment se demarquer
5. QUICK WINS : actions rapides pour gagner du terrain"""

        analyse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
        )

        return {**state, "analyse_concurrence": analyse, "erreur": ""}
    except Exception as e:
        return {**state, "analyse_concurrence": "", "erreur": f"Erreur concurrence : {str(e)}"}


def generer_rapport(state: SEOState) -> SEOState:
    try:
        system = """Tu es un consultant SEO senior.
Tu rediges des rapports SEO professionnels, structures et actionnables.
Tu reponds en francais. Tu termines TOUJOURS toutes tes sections."""

        prompt = f"""Genere un rapport SEO complet pour :

URL : {state['url']}
Type : {state['type_site']}
Secteur : {state['secteur']}
Mots-cles : {', '.join(state['mots_cles'])}

ANALYSE TECHNIQUE :
{state['analyse_technique']}

ANALYSE MOTS-CLES :
{state['analyse_mots_cles']}

ANALYSE CONCURRENCE :
{state['analyse_concurrence']}

Structure le rapport en 5 sections concises :
1. SCORE SEO GLOBAL (X/100) ET RESUME EXECUTIF
2. PROBLEMES CRITIQUES A CORRIGER (priorite haute)
3. OPTIMISATIONS RECOMMANDEES (priorite moyenne)
4. STRATEGIE MOTS-CLES (actions concretes)
5. PLAN D'ACTION 30/60/90 JOURS

Chaque section : bullets concis, actionnable, sans remplissage.
Termine toujours le PLAN D'ACTION."""

        rapport = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
        )

        # Extraire le score SEO
        score = 50
        for ligne in rapport.split("\n"):
            if "/100" in ligne and any(c.isdigit() for c in ligne):
                import re
                nombres = re.findall(r'\d+', ligne)
                if nombres:
                    score = min(int(nombres[0]), 100)
                    break

        return {**state, "rapport_seo": rapport, "score_seo": score, "erreur": ""}
    except Exception as e:
        return {**state, "rapport_seo": "", "score_seo": 0, "erreur": f"Erreur rapport : {str(e)}"}


def build_graph():
    graph = StateGraph(SEOState)
    graph.add_node("analyser_technique", analyser_technique)
    graph.add_node("analyser_mots_cles", analyser_mots_cles)
    graph.add_node("analyser_concurrence", analyser_concurrence)
    graph.add_node("generer_rapport", generer_rapport)

    graph.set_entry_point("analyser_technique")
    graph.add_edge("analyser_technique", "analyser_mots_cles")
    graph.add_edge("analyser_mots_cles", "analyser_concurrence")
    graph.add_edge("analyser_concurrence", "generer_rapport")
    graph.add_edge("generer_rapport", END)

    return graph.compile()