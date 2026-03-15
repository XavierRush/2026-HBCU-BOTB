"""Central configuration for the AISLED prototype."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    # If python-dotenv isn't installed, we can still run as long as env vars are set.
    def load_dotenv(*args, **kwargs):
        return False


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env from the repo root without overriding real environment variables.
load_dotenv(ENV_FILE, override=False)

DEBUG_MODE = os.getenv("DEBUG_MODE", "0").lower() in {"1", "true", "yes", "on"}
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

QUERY_TEMPLATES = [
    "What are the best {category} under ${price_ceiling}?",
    "Recommend a good {category} for someone on a budget.",
    "What {category} do most people buy online?",
    "Is {brand} {product_name} a good choice for {category}?",
    "How does {brand} {product_name} compare to {brand} {product_name}?",
]
