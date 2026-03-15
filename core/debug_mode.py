from __future__ import annotations

from core.product_schema import Product


def mock_query_response(product: Product, prompt: str) -> str:
    """Return a deterministic response that exercises the analyzer in debug mode."""
    prompt_lower = prompt.lower()

    # 1) Best-in-class query (no brand/product mention -> visibility flag false)
    if "best" in prompt_lower and "under" in prompt_lower:
        return (
            "For pet owners looking for the best collapsible dog crate, focus on durability, "
            "ventilation, and how easy it is to transport. A good crate has reinforced corners, "
            "a strong lock, and legs that keep it off the ground. Avoid listings that only mention "
            "color options and not structural strength."
        )

    # 2) Budget query (mentions brand but skips some features)
    if "budget" in prompt_lower:
        return (
            "For a budget-conscious shopper, the Rock Creek Crates Collapsible Dog Crate "
            "is compelling because it comes with a 10-year warranty and easy-carry handles. "
            "The listing could improve by calling out the stackable corner guards and the "
            "secondary butterfly latches, which are major trust factors for buyers."
        )

    # 3) Most-popular query (mentions crate generically, with a random hallucination)
    if "most people" in prompt_lower:
        return (
            "Most people end up choosing a collapsible crate that folds flat and has multiple "
            "locking mechanisms. A popular feature is a built-in food bowl, though not all crates "
            "actually include one — some listings incorrectly say they do. Always check the core "
            "dimensions and ventilation to avoid overheating."
        )

    # 4) Direct “good choice” query (mentions the product directly)
    if "good choice" in prompt_lower:
        return (
            "Yes, the Rock Creek Crates Collapsible Dog Crate is a solid choice for pet owners who "
            "want portability plus strength. It includes a lockable paddle latch, optimal venting, "
            "and a 10-year warranty — all key trust signals for buyers."
        )

    # 5) Comparison query (mentions the product + a mild hallucinated claim)
    if "compare" in prompt_lower:
        return (
            "Compared to a standard wire crate, the Rock Creek Crates Collapsible Dog Crate feels "
            "more premium because of its overbuilt door and stackable corner guards. Some users even "
            "say it folds small enough to fit in a backpack (though that claim isn't in the official specs)."
        )

    # Default fallback (shouldn't normally be hit)
    return (
        f"The Rock Creek Crates Collapsible Dog Crate is a dog crate priced at ${product.price:.2f}. "
        f"Key highlights include {product.key_features[0]}, {product.key_features[1]}, and {product.key_features[2]}. "
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
