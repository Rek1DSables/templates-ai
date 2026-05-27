# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = "claude-haiku-4-5-20251001"

# Trading
CAPITAL_INITIAL = 10000
STRATEGIES = ["Moyenne Mobile", "RSI", "Momentum"]
PERIODES = ["1mo", "3mo", "6mo", "1y"]
ACTIFS = ["BTC-USD", "ETH-USD", "AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "SP500"]

# Retry
MAX_RETRIES = 3
RETRY_DELAY = 5