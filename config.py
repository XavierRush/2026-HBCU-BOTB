"""Central configuration for the AI Visibility Analyzer prototype."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load .env from the repo root without overriding real environment variables.
load_dotenv(ENV_FILE, override=False)

DEBUG_MODE = os.getenv("DEBUG_MODE", "0").lower() in {"1", "true", "yes", "on"}
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
WEB_SEARCH_TOOL_NAME = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL_NAME", "web_search")
WEB_SEARCH_TOOL_TYPE = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL_TYPE", "web_search_20260209")
WEB_SEARCH_MAX_USES = int(os.getenv("ANTHROPIC_WEB_SEARCH_MAX_USES", "5"))

# Additional LLM API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")
MULTI_LLM_PROVIDERS = [
    provider.strip().lower()
    for provider in os.getenv("MULTI_LLM_PROVIDERS", "openai,gemini,perplexity").split(",")
    if provider.strip()
]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
PERPLEXITY_MODEL = os.getenv("PERPLEXITY_MODEL", "llama-3.1-sonar-large-128k-online")

QUERY_TEMPLATES = [
    "What are the best {category} under ${price_ceiling}?",
    "Recommend a good {category} for someone on a budget.",
    "What {category} do most people buy online?",
    "Is {brand} {product_name} a good choice for {category}?",
    "How does {brand} {product_name} compare to {brand} {product_name}?",
]
