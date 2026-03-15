from __future__ import annotations

try:
    import anthropic
except ImportError:  # pragma: no cover
    anthropic = None

from config import ANTHROPIC_API_KEY, DEBUG_MODE, MODEL_NAME, QUERY_TEMPLATES
from core.debug_mode import mock_query_response
from core.product_schema import Product


def build_queries(product: Product) -> list[str]:
    """Generate generalized, direct, and comparison-style queries."""
    price_ceiling = round(product.price * 1.25 / 10) * 10
    return [
        QUERY_TEMPLATES[0].format(category=product.category, price_ceiling=price_ceiling),
        QUERY_TEMPLATES[1].format(category=product.category),
        QUERY_TEMPLATES[2].format(category=product.category),
        QUERY_TEMPLATES[3].format(
            brand=product.brand,
            product_name=product.name,
            category=product.category,
        ),
        QUERY_TEMPLATES[4].format(
            brand=product.brand,
            product_name=product.name,
        ),
    ]


def query_llm(prompt: str) -> str:
    """Send a single query to Claude and return the text response."""
    if not ANTHROPIC_API_KEY or anthropic is None:
        raise RuntimeError(
            "Claude API client not available. Set DEBUG_MODE=1 or install the 'anthropic' package and provide ANTHROPIC_API_KEY."
        )

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def run_all_queries(product: Product) -> dict[str, str]:
    """Return a mapping of prompt to LLM response."""
    if DEBUG_MODE or not ANTHROPIC_API_KEY or anthropic is None:
        return {
            query: mock_query_response(product, query)
            for query in build_queries(product)
        }

    return {query: query_llm(query) for query in build_queries(product)}
