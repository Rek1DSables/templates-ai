import os
from dotenv import load_dotenv

load_dotenv()

# ─── Anthropic ────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME        = "claude-haiku-4-5-20251001"

# ─── Rapport ──────────────────────────────────────────────────────────────────
COMPANY_NAME = "Votre Entreprise"

# ─── Benchmarks sectoriels (ratios moyens par secteur) ────────────────────────
SECTOR_BENCHMARKS = {
    "Technologie": {
        "pe_ratio":        25.0,
        "debt_to_equity":  0.5,
        "current_ratio":   2.0,
        "gross_margin":    0.60,
        "roe":             0.20,
    },
    "Finance": {
        "pe_ratio":        12.0,
        "debt_to_equity":  2.0,
        "current_ratio":   1.2,
        "gross_margin":    0.40,
        "roe":             0.12,
    },
    "Santé": {
        "pe_ratio":        20.0,
        "debt_to_equity":  0.8,
        "current_ratio":   1.8,
        "gross_margin":    0.55,
        "roe":             0.15,
    },
    "Industrie": {
        "pe_ratio":        15.0,
        "debt_to_equity":  1.0,
        "current_ratio":   1.5,
        "gross_margin":    0.30,
        "roe":             0.10,
    },
    "Distribution": {
        "pe_ratio":        18.0,
        "debt_to_equity":  1.2,
        "current_ratio":   1.3,
        "gross_margin":    0.25,
        "roe":             0.14,
    },
}

SECTORS = list(SECTOR_BENCHMARKS.keys())

# ─── Retry Anthropic ──────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 5