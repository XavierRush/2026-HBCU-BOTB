from __future__ import annotations

import anthropic

from config import (
    ANTHROPIC_API_KEY,
    DEBUG_MODE,
    MODEL_NAME,
    QUERY_TEMPLATES,
    WEB_SEARCH_ALLOWED_CALLERS,
    WEB_SEARCH_TOOL_NAME,
    WEB_SEARCH_TOOL_TYPE,
)
from core.anthropic_rate_limit import create_rate_limited_message
from core.debug_mode import mock_query_response
from core.product_schema import Product

COMPETITOR_BRAND = "GUNNER"
COMPETITOR_NAME = "G1 Kennel Black"


def get_competitor_context(product: Product) -> dict[str, str]:
    """Return the comparison target for the selected product."""
    if product.brand == "Rock Creek Crates":
        return {
            "competitor_brand": COMPETITOR_BRAND,
            "competitor_name": COMPETITOR_NAME,
        }
    return {
        "competitor_brand": "Rock Creek Crates",
        "competitor_name": "Collapsible Dog Crate",
    }


def build_queries(product: Product) -> list[str]:
    """Generate robust shopping-style, direct, and head-to-head queries."""
    price_ceiling = round(product.price * 1.25 / 10) * 10
    competitor = get_competitor_context(product)
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
            category=product.category,
            **competitor,
        ),
        QUERY_TEMPLATES[5].format(
            brand=product.brand,
            product_name=product.name,
            category=product.category,
            **competitor,
        ),
    ]


def query_llm(prompt: str) -> str:
    """Send a single query to Claude and return the text response."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = create_rate_limited_message(
        client,
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
        tools=[
            {
                "type": WEB_SEARCH_TOOL_TYPE,
                "name": WEB_SEARCH_TOOL_NAME,
                "allowed_callers": WEB_SEARCH_ALLOWED_CALLERS,
            }
        ],
    )
    text_blocks = [
        block.text
        for block in message.content
        if getattr(block, "type", None) == "text" and getattr(block, "text", "")
    ]
    return "\n".join(text_blocks).strip()


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
