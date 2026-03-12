from __future__ import annotations

import json

import streamlit as st

from config import DEBUG_MODE
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.recommender import generate_recommendations

st.set_page_config(page_title="AI Visibility Analyzer", layout="wide")
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
            st.write("**AI Response:**")
            st.write(query_results[query])

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
