# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# OpenAI Whisper
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# ElevenLabs
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = "kENkNtk0xyzG09WW40xE"  # Marcel — voix française
ELEVENLABS_MODEL = "eleven_multilingual_v2"

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5

# Audio
SUPPORTED_AUDIO_FORMATS = ["mp3", "wav", "m4a", "ogg", "webm"]