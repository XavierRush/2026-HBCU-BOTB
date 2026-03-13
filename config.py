"""Central configuration for the AI Visibility Analyzer prototype."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"
ENV_VALUES = {
    key: value.strip()
    for key, value in dotenv_values(ENV_FILE).items()
    if value is not None and str(value).strip()
}


def _read_streamlit_secret(key: str) -> str | None:
    """Return a Streamlit secret when available without requiring Streamlit runtime."""
    try:
        import streamlit as st
    except Exception:
        return None

    try:
        value: Any = st.secrets[key]
    except Exception:
        return None

    return str(value).strip() if value is not None else None


def get_setting(key: str, default: str = "") -> str:
    """Resolve configuration from environment, then Streamlit secrets, then .env."""
    env_value = os.getenv(key)
    if env_value is not None and env_value.strip():
        return env_value.strip()

    secret_value = _read_streamlit_secret(key)
    if secret_value:
        return secret_value

    return ENV_VALUES.get(key, default)


DEBUG_MODE = get_setting("DEBUG_MODE", "0").lower() in {"1", "true", "yes", "on"}
ANTHROPIC_API_KEY = get_setting("ANTHROPIC_API_KEY", "")
MODEL_NAME = get_setting("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

QUERY_TEMPLATES = [
    "What are the best {category} under ${price_ceiling}?",
    "Recommend a good {category} for someone on a budget.",
    "What {category} do most people buy online?",
    "Is {brand} {product_name} a good choice for {category}?",
    "How does {brand} {product_name} compare to {brand} {product_name}?",
]
