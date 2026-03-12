from __future__ import annotations

from core.product_schema import Product


def mock_query_response(product: Product, prompt: str) -> str:
    """Return a deterministic response that exercises the analyzer in debug mode."""
    prompt_lower = prompt.lower()

    if "compare" in prompt_lower:
        return (
            f"{product.brand} {product.name} is often compared with other {product.category} "
            f"options in the same price range. It stands out for {product.key_features[0]}, "
            f"but shoppers may miss details like {product.key_features[-1]} if listings are sparse."
        )

    if "good choice" in prompt_lower:
        return (
            f"Yes, the {product.brand} {product.name} is a solid {product.category} choice for "
            f"buyers who want {product.key_features[0]} and a price near ${product.price:.2f}."
        )

    if "budget" in prompt_lower:
        return (
            f"For a budget-friendly {product.category}, shoppers often look for clear specs, "
            f"price, and availability. The {product.brand} {product.name} fits that range but "
            f"its {product.key_features[0]} should be described more clearly."
        )

    return (
        f"The {product.brand} {product.name} is a {product.category} priced at "
        f"${product.price:.2f}. Key highlights include {', '.join(product.key_features[:2])}. "
        f"It is currently listed as {product.availability}."
    )


def mock_recommendations(product: Product, analysis: dict[str, object]) -> str:
    """Return deterministic recommendations without calling Claude."""
    missing_features = analysis["missing_features"] or ["detailed feature wording"]
    top_missing = ", ".join(missing_features[:2])

    return f"""### Visibility Fixes
1. Put the exact product name `{product.name}` in the first sentence of the product page.
2. Repeat the category term `{product.category}` in headings, bullets, and metadata.
3. Add a short specs block that includes price, availability, and top features.

### Missing Feature Fixes
1. Call out these features more explicitly: {top_missing}.
2. Add a comparison table so AI systems can pick up structured facts more reliably.

### Hallucination Control
1. Keep one canonical product description and reuse it across your store, feeds, and social listings.

### Why Visibility Is Low
AI systems usually miss products when the listing lacks repeated, structured facts. This debug report suggests the page needs clearer product naming, stronger category language, and more explicit feature coverage."""
