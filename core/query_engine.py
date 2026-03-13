from __future__ import annotations

import anthropic

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
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def run_all_queries(product: Product) -> dict[str, str]:
    """Return a mapping of prompt to LLM response."""
    if DEBUG_MODE or not ANTHROPIC_API_KEY:
        return {
            query: mock_query_response(product, query)
            for query in build_queries(product)
        }

    return {query: query_llm(query) for query in build_queries(product)}


def run_multi_llm_queries(product: Product) -> dict[str, dict[str, str]]:
    """Return a mapping of prompt to responses from multiple LLMs."""
    from core.multi_llm_query import MultiLLMQueryEngine

    engine = MultiLLMQueryEngine()
    return engine.query_product_recommendations(product)
