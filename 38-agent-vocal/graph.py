# graph.py
import time
import anthropic
from langgraph.graph import StateGraph, END
from typing import TypedDict
from config import (
    MODEL_NAME, ANTHROPIC_API_KEY,
    MAX_RETRIES, RETRY_DELAY,
)

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


class VocalState(TypedDict):
    audio_bytes: bytes
    audio_format: str
    transcription: str
    intention: str
    categorie: str
    reponse_texte: str
    audio_reponse: bytes
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


def transcrire_audio(state: VocalState) -> VocalState:
    try:
        from openai import OpenAI
        from config import OPENAI_API_KEY
        import io

        openai_client = OpenAI(api_key=OPENAI_API_KEY)

        audio_file = io.BytesIO(state["audio_bytes"])
        audio_file.name = f"audio.{state['audio_format']}"

        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="fr",
        )

        return {**state, "transcription": transcription.text, "erreur": ""}
    except Exception as e:
        return {**state, "transcription": "", "erreur": f"Erreur transcription : {str(e)}"}


def analyser_intention(state: VocalState) -> VocalState:
    try:
        system = """Tu es un agent d'analyse d'intention pour un support vocal.
Tu analyses la transcription d'un appel entrant et tu identifies l'intention et la categorie.
Tu reponds UNIQUEMENT avec ce JSON sans backticks :
{"intention": "description courte de l'intention", "categorie": "support|information|rdv|plainte|autre", "urgence": "haute|normale|basse"}"""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": f"Transcription : {state['transcription']}"}],
        )

        import json
        reponse_clean = reponse.strip()
        if reponse_clean.startswith("```"):
            reponse_clean = reponse_clean.split("```")[1]
            if reponse_clean.startswith("json"):
                reponse_clean = reponse_clean[4:]
        reponse_clean = reponse_clean.strip()

        data = json.loads(reponse_clean)

        return {
            **state,
            "intention": data.get("intention", ""),
            "categorie": data.get("categorie", "autre"),
            "erreur": "",
        }
    except Exception as e:
        return {**state, "intention": "", "categorie": "autre", "erreur": f"Erreur intention : {str(e)}"}


def generer_reponse(state: VocalState) -> VocalState:
    try:
        system = """Tu es un agent vocal professionnel et bienveillant.
Tu reponds aux appels entrants avec une voix claire, concise et utile.
Ta reponse sera synthetisee en audio donc :
- Pas de bullet points ni de markdown
- Phrases courtes et naturelles
- Ton chaleureux et professionnel
- Maximum 100 mots
- Tu reponds toujours en francais"""

        prompt = f"""Transcription de l'appel entrant : {state['transcription']}

Intention detectee : {state['intention']}
Categorie : {state['categorie']}

Redige une reponse vocale naturelle et professionnelle."""

        reponse = invoke_with_retry(
            system=system,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
        )

        return {**state, "reponse_texte": reponse, "erreur": ""}
    except Exception as e:
        return {**state, "reponse_texte": "", "erreur": f"Erreur reponse : {str(e)}"}


def synthetiser_audio(state: VocalState) -> VocalState:
    try:
        from gtts import gTTS
        import io

        tts = gTTS(text=state["reponse_texte"], lang="fr", slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)

        return {**state, "audio_reponse": audio_buffer.read(), "erreur": ""}
    except Exception as e:
        return {**state, "audio_reponse": b"", "erreur": f"Erreur synthese : {str(e)}"}

        response = requests.post(url, headers=headers, json=payload, timeout=30)

        if response.status_code != 200:
            return {**state, "audio_reponse": b"", "erreur": f"Erreur ElevenLabs : {response.text}"}

        return {**state, "audio_reponse": response.content, "erreur": ""}
    except Exception as e:
        return {**state, "audio_reponse": b"", "erreur": f"Erreur synthese : {str(e)}"}


def build_graph():
    graph = StateGraph(VocalState)
    graph.add_node("transcrire_audio", transcrire_audio)
    graph.add_node("analyser_intention", analyser_intention)
    graph.add_node("generer_reponse", generer_reponse)
    graph.add_node("synthetiser_audio", synthetiser_audio)

    graph.set_entry_point("transcrire_audio")
    graph.add_edge("transcrire_audio", "analyser_intention")
    graph.add_edge("analyser_intention", "generer_reponse")
    graph.add_edge("generer_reponse", "synthetiser_audio")
    graph.add_edge("synthetiser_audio", END)

    return graph.compile()