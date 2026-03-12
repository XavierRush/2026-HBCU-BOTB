from __future__ import annotations

import re

from sentence_transformers import SentenceTransformer, util

from core.product_schema import Product

model = SentenceTransformer("all-MiniLM-L6-v2")


def check_visibility(product: Product, llm_response: str) -> dict[str, object]:
    """Compare an LLM response against the source product details."""
    response_lower = llm_response.lower()
    mentioned = product.name.lower() in response_lower or product.brand.lower() in response_lower

    product_embedding = model.encode(product.description, convert_to_tensor=True)
    response_embedding = model.encode(llm_response, convert_to_tensor=True)
    similarity = float(util.cos_sim(product_embedding, response_embedding))

    missing_features = [
        feature for feature in product.key_features if feature.lower() not in response_lower
    ]

    sentences = re.split(r"(?<=[.!?])\s+", llm_response)
    hallucinated_claims = []
    for sentence in sentences:
        lowered_sentence = sentence.lower()
        if product.brand.lower() in lowered_sentence or product.name.lower() in lowered_sentence:
            sentence_embedding = model.encode(sentence, convert_to_tensor=True)
            score = float(util.cos_sim(product_embedding, sentence_embedding))
            if score < 0.25:
                hallucinated_claims.append(sentence)

    return {
        "mentioned": mentioned,
        "similarity_score": round(similarity, 3),
        "missing_features": missing_features,
        "hallucinated_claims": hallucinated_claims,
    }


def aggregate_results(product: Product, query_results: dict[str, str]) -> dict[str, object]:
    """Compute summary metrics across all generated queries."""
    analyses = {
        query: check_visibility(product, response)
        for query, response in query_results.items()
    }

    visibility_rate = sum(1 for result in analyses.values() if result["mentioned"]) / len(analyses)
    avg_similarity = sum(result["similarity_score"] for result in analyses.values()) / len(analyses)
    all_missing = list(
        {
            feature
            for result in analyses.values()
            for feature in result["missing_features"]
        }
    )
    all_hallucinations = [
        claim
        for result in analyses.values()
        for claim in result["hallucinated_claims"]
    ]

    return {
        "product_name": product.name,
        "visibility_rate": round(visibility_rate, 2),
        "avg_accuracy_score": round(avg_similarity, 3),
        "missing_features": all_missing,
        "hallucinated_claims": all_hallucinations,
        "per_query": analyses,
    }
