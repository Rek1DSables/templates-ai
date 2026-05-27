# 38 — Agent Vocal Entrant AI

Pipeline de traitement d'appels vocaux entrants. LangGraph orchestre 4 nœuds en séquence : transcription audio via Whisper (OpenAI), analyse de l'intention avec Claude, génération d'une réponse vocale naturelle, synthèse audio via ElevenLabs (gTTS en développement).

## Stack

- **LangGraph** — orchestration séquentielle des 4 agents
- **Whisper (OpenAI)** — transcription audio vers texte
- **Anthropic Claude** — analyse intention + génération réponse
- **ElevenLabs** — synthèse vocale production (voix française)
- **gTTS** — synthèse vocale développement (gratuit)
- **Streamlit** — interface utilisateur

## Fonctionnalités

- Upload fichier audio (mp3, wav, m4a, ogg, webm)
- Transcription automatique via Whisper en français
- Analyse de l'intention et catégorisation (support, information, rdv, plainte, autre)
- Génération d'une réponse vocale naturelle (max 100 mots, sans markdown)
- Synthèse audio et lecture directe dans l'interface
- Téléchargement de la réponse audio
- Retry automatique (3 tentatives, 5s) sur erreur overload Anthropic

## Structure

```
38-agent-vocal/
├── app.py          # Interface Streamlit
├── graph.py        # LangGraph 4 noeuds
├── config.py       # Configuration centralisee
├── requirements.txt
├── .env
└── README.md
```

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Variables d'environnement

```
ANTHROPIC_API_KEY=ta_clé_ici
OPENAI_API_KEY=ta_clé_openai
ELEVENLABS_API_KEY=ta_clé_elevenlabs
```

## Notes

- En développement : gTTS (gratuit) remplace ElevenLabs
- En production : ElevenLabs nécessite un plan Starter (5$/mois minimum)
- Pour activer ElevenLabs : remplacer `synthetiser_audio` dans `graph.py` et renseigner `ELEVENLABS_VOICE_ID` dans `config.py`
- Whisper supporte le français nativement (language="fr")

## Données de test

Enregistrer un message vocal simulant un appel entrant :
"Bonjour, je n'arrive pas à me connecter à mon compte depuis ce matin, pouvez-vous m'aider ?"

## Modèle utilisé

`claude-haiku-4-5-20251001` + `whisper-1` (OpenAI)