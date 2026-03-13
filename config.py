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
MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
ANTHROPIC_INPUT_TOKENS_PER_MINUTE = int(
    os.getenv("ANTHROPIC_INPUT_TOKENS_PER_MINUTE", "30000")
)
WEB_SEARCH_TOOL_TYPE = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL_TYPE", "web_search_20260209")
WEB_SEARCH_TOOL_NAME = os.getenv("ANTHROPIC_WEB_SEARCH_TOOL_NAME", "web_search")
WEB_SEARCH_ALLOWED_CALLERS = [
    caller.strip()
    for caller in os.getenv("ANTHROPIC_WEB_SEARCH_ALLOWED_CALLERS", "direct").split(",")
    if caller.strip()
]

# Additional LLM API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY", "")

QUERY_TEMPLATES = [
    "What are the best {category} options under ${price_ceiling} for shoppers who care about durability, warranty, and delivery readiness?",
    "Recommend a {category} for a buyer comparing safety, portability, and long-term value.",
    "Which {category} is most often recommended online for buyers who want clear specs and trustworthy product details?",
    "Is {brand} {product_name} a good choice for someone shopping for a {category} and weighing quality, shipping, and warranty coverage?",
    "Compare {brand} {product_name} vs {competitor_brand} {competitor_name} for a shopper choosing a {category}. Focus on construction, portability, warranty, and use case fit.",
    "Between {brand} {product_name} and {competitor_brand} {competitor_name}, which is the better pick for a {category} buyer who wants trustworthy specs and fewer tradeoffs?",
]
