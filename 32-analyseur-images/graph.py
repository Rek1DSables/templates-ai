# graph.py
import time
import base64
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import MODEL_NAME, ANTHROPIC_API_KEY, MAX_RETRIES, RETRY_DELAY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class ImageState(TypedDict):
    image_base64: str
    media_type: str
    nom_fichier: str
    description: str
    donnees_extraites: str
    insights: str
    erreur: str


def invoke_with_retry_vision(prompt: str, image_base64: str, media_type: str) -> str:
    for attempt in range(MAX_RETRIES):
        try:
            response = client.messages.create(
                model=MODEL_NAME,
                max_tokens=1500,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )
            return response.content[0].text
        except anthropic.APIStatusError as e:
            if "overloaded" in str(e).lower() and attempt < MAX_RETRIES - 1:
                print(f"[Retry {attempt + 1}/{MAX_RETRIES}] Modele surcharge, attente {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)
            else:
                raise


def decrire_image(state: ImageState) -> ImageState:
    try:
        prompt = """Analyse cette image en detail et fournis une description complete.

Ta description doit couvrir :
1. NATURE DU DOCUMENT : type d'image (facture, schema, screenshot, photo, graphique, etc.)
2. CONTENU PRINCIPAL : ce que montre l'image en detail
3. ELEMENTS VISUELS : couleurs, mise en page, structure, textes visibles
4. CONTEXTE : contexte professionnel ou usage apparent de ce document

Sois precis et exhaustif."""

        description = invoke_with_retry_vision(prompt, state["image_base64"], state["media_type"])
        return {**state, "description": description, "erreur": ""}
    except Exception as e:
        return {**state, "description": "", "erreur": f"Erreur description : {str(e)}"}


def extraire_donnees(state: ImageState) -> ImageState:
    try:
        prompt = """Extrait toutes les donnees structurees visibles dans cette image.

Selon le type de document, extrait :
- Textes, titres, labels
- Nombres, montants, dates, references
- Tableaux et leurs valeurs
- Listes et elements enumeres
- Noms, entreprises, contacts
- Tout autre information exploitable

Format de sortie :
CATEGORIE : valeur extraite
(une information par ligne, categories en majuscules)

Si une categorie n'est pas applicable, ne la mentionne pas."""

        donnees = invoke_with_retry_vision(prompt, state["image_base64"], state["media_type"])
        return {**state, "donnees_extraites": donnees, "erreur": ""}
    except Exception as e:
        return {**state, "donnees_extraites": "", "erreur": f"Erreur extraction : {str(e)}"}


def generer_insights(state: ImageState) -> ImageState:
    try:
        prompt = """Analyse cette image d'un point de vue professionnel et fournis des insights actionnables.

Tes insights doivent couvrir :
1. POINTS CLES : observations importantes sur le contenu
2. ANOMALIES OU ALERTES : elements inhabituels, erreurs, incohérences detectees
3. RECOMMANDATIONS : actions concretes a entreprendre suite a cette analyse
4. USAGES POSSIBLES : comment exploiter ces informations

Sois concret et actionnable. Si l'image est une photo sans contenu professionnel, adapte l'analyse au contexte visible."""

        insights = invoke_with_retry_vision(prompt, state["image_base64"], state["media_type"])
        return {**state, "insights": insights, "erreur": ""}
    except Exception as e:
        return {**state, "insights": "", "erreur": f"Erreur insights : {str(e)}"}


def build_graph():
    graph = StateGraph(ImageState)
    graph.add_node("decrire_image", decrire_image)
    graph.add_node("extraire_donnees", extraire_donnees)
    graph.add_node("generer_insights", generer_insights)

    graph.set_entry_point("decrire_image")
    graph.add_edge("decrire_image", "extraire_donnees")
    graph.add_edge("extraire_donnees", "generer_insights")
    graph.add_edge("generer_insights", END)

    return graph.compile()