from __future__ import annotations

import html
import json

import streamlit as st

from config import DEBUG_MODE
from core.multi_llm_query import MultiLLMQueryEngine
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.recommender import generate_recommendations

st.set_page_config(page_title="AI Visibility Analyzer", layout="wide")

st.markdown(
    """
    <style>
    .llm-card {
        border: 1px solid rgba(15, 23, 42, 0.08);
        border-radius: 18px;
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(248,250,252,0.96));
        box-shadow: 0 14px 34px rgba(15, 23, 42, 0.08);
        min-height: 320px;
        overflow: hidden;
    }
    .llm-card__header {
        padding: 0.9rem 1rem 0.75rem;
        border-bottom: 1px solid rgba(15, 23, 42, 0.08);
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #0f172a;
        background: rgba(241, 245, 249, 0.85);
    }
    .llm-card__body {
        height: 250px;
        overflow-y: auto;
        padding: 1rem;
        color: #1e293b;
        line-height: 1.55;
        white-space: pre-wrap;
        font-size: 0.95rem;
    }
    .llm-card__body::-webkit-scrollbar {
        width: 8px;
    }
    .llm-card__body::-webkit-scrollbar-thumb {
        background: rgba(148, 163, 184, 0.8);
        border-radius: 999px;
    }
    .llm-card--placeholder .llm-card__body {
        background:
            linear-gradient(90deg, rgba(191, 219, 254, 0.14), rgba(224, 231, 255, 0.32), rgba(191, 219, 254, 0.14));
        background-size: 220% 100%;
        animation: llm-placeholder-shimmer 2.4s ease-in-out infinite;
    }
    .llm-placeholder-line {
        height: 0.9rem;
        border-radius: 999px;
        margin-bottom: 0.8rem;
        background: rgba(148, 163, 184, 0.16);
    }
    .llm-placeholder-line:last-child {
        margin-bottom: 0;
    }
    @keyframes llm-placeholder-shimmer {
        0% { background-position: 200% 0; }
        100% { background-position: -20% 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


PROVIDER_ORDER = [
    ("claude", "Claude Web Search"),
    ("openai", "ChatGPT"),
    ("gemini", "Gemini"),
    ("perplexity", "Perplexity"),
]


def render_llm_card(title: str, content: str | None, placeholder: bool = False) -> None:
    """Render a scrollable response card or a placeholder shimmer."""
    if placeholder:
        body = "".join(
            f"<div class='llm-placeholder-line' style='width: {width};'></div>"
            for width in ("92%", "84%", "88%", "76%", "81%", "69%")
        )
        card_class = "llm-card llm-card--placeholder"
    else:
        safe_content = html.escape(content or "")
        body = safe_content if safe_content else "<span style='opacity:0.6;'>No response returned.</span>"
        card_class = "llm-card"

    st.markdown(
        f"""
        <div class="{card_class}">
            <div class="llm-card__header">{html.escape(title)}</div>
            <div class="llm-card__body">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.title("AI Visibility Analyzer")
st.caption("Understand why your product is not showing up in AI-assisted shopping results.")
if DEBUG_MODE:
    st.info("Debug mode is enabled. Claude calls are replaced with mock responses.")

with st.sidebar:
    st.header("Enter Your Product")
    name = st.text_input("Product Name", "MechPro K75 Keyboard")
    brand = st.text_input("Brand", "MechPro")
    category = st.text_input("Category", "gaming keyboard")
    price = st.number_input("Price ($)", value=89.99)
    features_raw = st.text_area(
        "Key Features (one per line)",
        "mechanical switches\nRGB backlight\nTKL layout\nUSB-C",
    )
    description = st.text_area(
        "Product Description",
        "The MechPro K75 is a tenkeyless mechanical keyboard with Cherry MX Red switches, "
        "per-key RGB lighting, and a detachable USB-C cable. Built for gamers who want a "
        "compact, fast, and reliable typing experience.",
    )
    availability = st.selectbox("Availability", ["in stock", "out of stock"])
    run = st.button("Analyze Visibility", type="primary")

if run:
    product = Product(
        name=name,
        brand=brand,
        category=category,
        price=price,
        key_features=[feature.strip() for feature in features_raw.splitlines() if feature.strip()],
        description=description,
        availability=availability,
    )

    with st.spinner("Querying AI models..."):
        query_results = run_all_queries(product)
        multi_llm_engine = MultiLLMQueryEngine()
        multi_llm_results = multi_llm_engine.query_product_recommendations(product)

    available_multi_llms = set(multi_llm_engine.available_provider_names())

    with st.spinner("Running NLP analysis..."):
        analysis = aggregate_results(product, query_results)

    with st.spinner("Generating recommendations..."):
        recommendations = generate_recommendations(product, analysis)

    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Visibility Rate",
        f"{analysis['visibility_rate'] * 100:.0f}%",
        help="How often the AI mentioned your product across all queries",
    )
    col2.metric(
        "Accuracy Score",
        f"{analysis['avg_accuracy_score']:.2f}/1.0",
        help="Semantic similarity between AI descriptions and your actual product data",
    )
    col3.metric(
        "Missing Features",
        len(analysis["missing_features"]),
        help="Key features the AI failed to mention",
    )

    st.divider()
    st.subheader("Query-by-Query Breakdown")
    for query, result in analysis["per_query"].items():
        mention_label = "Yes" if result["mentioned"] else "No"
        with st.expander(f"{mention_label} Mention: {query}"):
            st.write(f"**Mentioned:** {mention_label}")
            st.write(f"**Similarity Score:** {result['similarity_score']}")
            if result["missing_features"]:
                st.write(f"**Missing Features:** {', '.join(result['missing_features'])}")
            if result["hallucinated_claims"]:
                st.warning("Potential hallucinations detected:")
                for claim in result["hallucinated_claims"]:
                    st.write(f"- {claim}")
            st.write("**LLM Responses:**")
            card_columns = st.columns(len(PROVIDER_ORDER))
            query_multi_llm_results = multi_llm_results.get(query, {})
            for column, (provider_key, provider_title) in zip(card_columns, PROVIDER_ORDER):
                with column:
                    if provider_key == "claude":
                        render_llm_card(provider_title, query_results[query])
                    else:
                        render_llm_card(
                            provider_title,
                            query_multi_llm_results.get(provider_key),
                            placeholder=provider_key not in available_multi_llms,
                        )

    st.divider()
    st.subheader("Recommendations to Improve Visibility")
    st.markdown(recommendations)

    st.divider()
    export_data = {
        "product": product.model_dump(mode="json"),
        "analysis": analysis,
        "recommendations": recommendations,
    }
    st.download_button(
        "Download Full Report (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name=f"{brand}_{name}_visibility_report.json",
        mime="application/json",
    )
