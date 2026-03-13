from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from config import DEBUG_MODE
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.recommender import generate_recommendations

PRODUCT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_products.json"
ROCK_CREEK_BRAND = "Rock Creek Crates"


def load_demo_products() -> list[Product]:
    """Load the seeded demo products from disk."""
    with PRODUCT_DATA_PATH.open(encoding="utf-8") as file:
        raw_products = json.load(file)
    return [Product.model_validate(item) for item in raw_products]


def rock_creek_products() -> list[Product]:
    """Return the Rock Creek Crates products used in the main selector."""
    return [
        product
        for product in load_demo_products()
        if product.brand == ROCK_CREEK_BRAND
    ]


def render_product_card(product: Product, selected: bool) -> None:
    """Render a selectable product card."""
    availability_class = "product-card__status--in" if product.availability == "in stock" else "product-card__status--out"
    selected_class = " product-card--selected" if selected else ""
    feature_list = "".join(
        f"<span class='product-card__pill'>{feature}</span>"
        for feature in product.key_features[:3]
    )
    st.markdown(
        f"""
        <div class="product-card{selected_class}">
            <div class="product-card__eyebrow">{product.category}</div>
            <div class="product-card__title">{product.name}</div>
            <div class="product-card__meta">
                <span>${product.price:,.0f}</span>
                <span class="product-card__status {availability_class}">{product.availability}</span>
            </div>
            <div class="product-card__features">{feature_list}</div>
            <div class="product-card__description">{product.description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="AISLED", layout="wide")
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        display: none;
    }
    .stApp {
        background:
            radial-gradient(circle at top left, rgba(218, 165, 32, 0.18), transparent 30%),
            linear-gradient(180deg, #f7f3ea 0%, #efe6d6 100%);
    }
    .product-card {
        border: 1px solid rgba(113, 75, 33, 0.16);
        border-radius: 20px;
        background: rgba(255, 250, 242, 0.9);
        box-shadow: 0 14px 34px rgba(87, 61, 28, 0.08);
        padding: 1rem 1rem 1.1rem;
        margin-bottom: 0.9rem;
    }
    .product-card--selected {
        border-color: #7a4b1f;
        box-shadow: 0 18px 40px rgba(122, 75, 31, 0.18);
        background: linear-gradient(180deg, rgba(255,255,255,0.98), rgba(246,231,206,0.98));
    }
    .product-card__eyebrow {
        font-size: 0.75rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #8a5a2b;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .product-card__title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #2f2418;
        margin-bottom: 0.45rem;
    }
    .product-card__meta {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        color: #513a25;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    .product-card__status {
        border-radius: 999px;
        padding: 0.2rem 0.55rem;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.04em;
    }
    .product-card__status--in {
        background: rgba(53, 94, 59, 0.12);
        color: #355e3b;
    }
    .product-card__status--out {
        background: rgba(130, 52, 36, 0.12);
        color: #823424;
    }
    .product-card__features {
        display: flex;
        flex-wrap: wrap;
        gap: 0.4rem;
        margin-bottom: 0.8rem;
    }
    .product-card__pill {
        border-radius: 999px;
        background: rgba(122, 75, 31, 0.09);
        color: #6a421d;
        padding: 0.22rem 0.55rem;
        font-size: 0.76rem;
        font-weight: 600;
    }
    .product-card__description {
        color: #4a3928;
        line-height: 1.55;
        font-size: 0.93rem;
    }
    .product-detail {
        border: 1px solid rgba(113, 75, 33, 0.16);
        border-radius: 24px;
        background: rgba(255, 252, 247, 0.88);
        box-shadow: 0 18px 46px rgba(87, 61, 28, 0.1);
        padding: 1.4rem;
        margin-bottom: 1rem;
    }
    .product-detail__label {
        font-size: 0.8rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #8a5a2b;
        font-weight: 700;
        margin-bottom: 0.35rem;
    }
    .product-detail__title {
        font-size: 1.8rem;
        color: #2d2115;
        font-weight: 800;
        margin-bottom: 0.35rem;
    }
    .product-detail__subtitle {
        color: #5a4330;
        margin-bottom: 1rem;
    }
    .product-detail__features {
        margin: 1rem 0;
        color: #3f3123;
    }
    .product-detail__features li {
        margin-bottom: 0.35rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("AISLED:")
st.caption("Understand why your product is not showing up in AI-assisted shopping results.")
if DEBUG_MODE:
    st.info("Debug mode is enabled. Claude calls are replaced with mock responses.")

products = rock_creek_products()
if not products:
    st.error("No Rock Creek Crates products were found in data/sample_products.json.")
    st.stop()

default_product = products[0]
selected_url = st.session_state.get("selected_product_url", default_product.url or default_product.name)
selected_product = next(
    (product for product in products if (product.url or product.name) == selected_url),
    default_product,
)
st.session_state["selected_product_url"] = selected_product.url or selected_product.name

selector_col, detail_col = st.columns([1.05, 1.95], gap="large")

with selector_col:
    st.subheader("Choose a Rock Creek product")
    st.caption("Pick one of the three live demo products to run the visibility analysis.")
    for product in products:
        render_product_card(product, selected=(product.url == selected_product.url))
        if st.button(
            "Selected" if product.url == selected_product.url else "Select Product",
            key=f"select-{product.url or product.name}",
            use_container_width=True,
            type="primary" if product.url == selected_product.url else "secondary",
        ):
            st.session_state["selected_product_url"] = product.url or product.name
            st.rerun()

with detail_col:
    st.markdown(
        f"""
        <div class="product-detail">
            <div class="product-detail__label">Selected Product</div>
            <div class="product-detail__title">{selected_product.name}</div>
            <div class="product-detail__subtitle">
                {selected_product.brand} · {selected_product.category} · ${selected_product.price:,.0f}
            </div>
            <div>{selected_product.description}</div>
            <ul class="product-detail__features">
                {''.join(f"<li>{feature}</li>" for feature in selected_product.key_features)}
            </ul>
            <div><strong>Availability:</strong> {selected_product.availability}</div>
            <div><strong>Product URL:</strong> <a href="{selected_product.url}" target="_blank">{selected_product.url}</a></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    run = st.button("Analyze Visibility", type="primary", use_container_width=True)

if run:
    product = selected_product

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
        file_name=f"{product.brand}_{product.name}_visibility_report.json",
        mime="application/json",
    )
