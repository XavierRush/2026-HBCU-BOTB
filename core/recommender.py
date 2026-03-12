from __future__ import annotations

import anthropic

from config import ANTHROPIC_API_KEY, DEBUG_MODE, MODEL_NAME
from core.debug_mode import mock_recommendations
from core.product_schema import Product


def generate_recommendations(product: Product, analysis: dict[str, object]) -> str:
    """Ask Claude for actionable recommendations based on the analysis."""
    if DEBUG_MODE or not ANTHROPIC_API_KEY:
        return mock_recommendations(product, analysis)

    missing = ", ".join(analysis["missing_features"]) or "none detected"
    hallucinations = "\n".join(analysis["hallucinated_claims"]) or "none detected"

    prompt = f"""
You are an AI visibility consultant helping a small business improve how their product
appears in AI assistant responses.

Product: {product.name} by {product.brand}
Category: {product.category}
Price: ${product.price}
Description: {product.description}
Key Features: {", ".join(product.key_features)}

Analysis Results:
- Visibility Rate (how often AI mentioned the product): {analysis["visibility_rate"] * 100:.0f}%
- Accuracy Score (semantic similarity to real product data): {analysis["avg_accuracy_score"]}
- Features missing from AI responses: {missing}
- Potentially hallucinated claims about this product: {hallucinations}

Please provide:
1. Three specific changes the business can make to their product page or description to improve AI visibility
2. Two changes to address the missing features above
3. One action to correct any hallucinated claims
4. A plain-language explanation of why this product is not showing up in AI results

Be specific and actionable. Format as numbered lists under clear headers.
""".strip()

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model=MODEL_NAME,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text
