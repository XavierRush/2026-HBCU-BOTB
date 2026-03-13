from __future__ import annotations

import json
from statistics import mean

import streamlit as st

from config import DEBUG_MODE
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.recommender import generate_recommendations

st.set_page_config(page_title="AI Visibility Analyzer", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(233, 183, 123, 0.22), transparent 30%),
                linear-gradient(180deg, #fff8ef 0%, #f7efe4 100%);
        }
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2.5rem;
            max-width: 1440px;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #161616 0%, #26201a 100%);
        }
        [data-testid="stSidebar"] * {
            color: #f8efe3;
        }
        .hero-card,
        .metric-card,
        .section-card,
        .query-card {
            border: 1px solid rgba(22, 22, 22, 0.08);
            border-radius: 22px;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: 0 20px 40px rgba(54, 40, 22, 0.08);
            backdrop-filter: blur(10px);
        }
        .hero-card {
            padding: 1.5rem 1.6rem;
            margin-bottom: 1rem;
        }
        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.72rem;
            color: #8f5b2e;
            font-weight: 700;
        }
        .hero-title {
            font-size: 2.2rem;
            line-height: 1.05;
            margin: 0.35rem 0 0.45rem;
            color: #1d160f;
            font-weight: 700;
        }
        .hero-copy {
            color: #5f554b;
            max-width: 48rem;
            font-size: 1rem;
        }
        .metric-card {
            padding: 1rem 1.1rem;
            min-height: 144px;
        }
        .metric-label {
            color: #7b6b5d;
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            font-weight: 700;
        }
        .metric-value {
            font-size: 2rem;
            line-height: 1;
            font-weight: 700;
            color: #161616;
            margin: 0.4rem 0 0.55rem;
        }
        .metric-note {
            color: #5f554b;
            font-size: 0.95rem;
        }
        .section-card {
            padding: 1.1rem 1.2rem;
            margin-top: 1rem;
        }
        .section-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #161616;
            margin-bottom: 0.25rem;
        }
        .section-copy {
            color: #675a4d;
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
        }
        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.6rem;
        }
        .pill {
            background: #f5ebdf;
            color: #6e5335;
            border-radius: 999px;
            padding: 0.32rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 600;
        }
        .query-card {
            padding: 0.9rem 1rem;
            margin-bottom: 0.85rem;
        }
        .query-topline {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        .query-title {
            font-weight: 700;
            color: #1e1a16;
            font-size: 1rem;
        }
        .query-badge {
            border-radius: 999px;
            padding: 0.26rem 0.7rem;
            font-size: 0.8rem;
            font-weight: 700;
            white-space: nowrap;
        }
        .query-badge.good {
            background: rgba(40, 138, 84, 0.14);
            color: #1f6c42;
        }
        .query-badge.warn {
            background: rgba(194, 111, 34, 0.16);
            color: #9a5418;
        }
        .query-meta {
            color: #6a5c4d;
            font-size: 0.92rem;
        }
        .stExpander {
            border: 1px solid rgba(22, 22, 22, 0.08);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.72);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(label: str, value: str, note: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-title">{title}</div>
        <div class="section-copy">{copy}</div>
        """,
        unsafe_allow_html=True,
    )


def render_pills(items: list[str], empty_label: str) -> None:
    values = items or [empty_label]
    pills = "".join(f'<span class="pill">{item}</span>' for item in values)
    st.markdown(f'<div class="pill-row">{pills}</div>', unsafe_allow_html=True)


def render_query_summary(query: str, result: dict[str, object]) -> None:
    badge_label = "Mentioned" if result["mentioned"] else "Not mentioned"
    badge_class = "good" if result["mentioned"] else "warn"
    missing_count = len(result["missing_features"])
    hallucination_count = len(result["hallucinated_claims"])
    st.markdown(
        f"""
        <div class="query-card">
            <div class="query-topline">
                <div class="query-title">{query}</div>
                <div class="query-badge {badge_class}">{badge_label}</div>
            </div>
            <div class="query-meta">
                Similarity score: {result["similarity_score"]} | Missing features: {missing_count} | Potential hallucinations: {hallucination_count}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


inject_styles()
st.markdown(
    """
    <div class="hero-card">
        <div class="hero-eyebrow">Visibility Dashboard</div>
        <div class="hero-title">AI Visibility Analyzer</div>
        <div class="hero-copy">
            Diagnose how AI assistants describe your product, spot missing details quickly,
            and review structured recommendations in expandable sections.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)
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

    per_query_results = list(analysis["per_query"].values())
    mentioned_queries = sum(1 for result in per_query_results if result["mentioned"])
    hallucination_count = len(analysis["hallucinated_claims"])
    strongest_query_score = max(result["similarity_score"] for result in per_query_results)
    weakest_query_score = min(result["similarity_score"] for result in per_query_results)
    average_missing_per_query = mean(len(result["missing_features"]) for result in per_query_results)

    summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
    with summary_col1:
        render_metric_card(
            "Visibility Rate",
            f"{analysis['visibility_rate'] * 100:.0f}%",
            "How often the product was explicitly mentioned across the test prompts.",
        )
    with summary_col2:
        render_metric_card(
            "Accuracy Score",
            f"{analysis['avg_accuracy_score']:.2f}/1.0",
            "Average semantic similarity between your source details and AI responses.",
        )
    with summary_col3:
        render_metric_card(
            "Missing Features",
            str(len(analysis["missing_features"])),
            f"About {average_missing_per_query:.1f} product details were missed per query on average.",
        )
    with summary_col4:
        render_metric_card(
            "Risk Flags",
            str(hallucination_count),
            "Potential hallucinated claims detected in product-related response sentences.",
        )

    left_col, right_col = st.columns([1.45, 1], gap="large")

    with left_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Query Performance",
            "Review the full search set in a tighter dashboard format, then expand any query for detailed evidence.",
        )
        for query, result in analysis["per_query"].items():
            render_query_summary(query, result)
            with st.expander(f"Open query detail: {query}"):
                st.write(f"Mentioned: {'Yes' if result['mentioned'] else 'No'}")
                st.write(f"Similarity score: {result['similarity_score']}")
                st.write(
                    f"Missing features: {', '.join(result['missing_features']) if result['missing_features'] else 'None'}"
                )
                if result["hallucinated_claims"]:
                    st.warning("Potential hallucinations detected:")
                    for claim in result["hallucinated_claims"]:
                        st.write(f"- {claim}")
                else:
                    st.success("No hallucinated product claims were flagged for this response.")
                st.write("AI response")
                st.write(query_results[query])
        st.markdown("</div>", unsafe_allow_html=True)

    with right_col:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        render_section_header(
            "Snapshot",
            "A compact product profile so the analysis has clear business context right next to the metrics.",
        )
        st.write(f"Product: {product.name}")
        st.write(f"Brand: {product.brand}")
        st.write(f"Category: {product.category}")
        st.write(f"Price: ${product.price:.2f}")
        st.write(f"Availability: {product.availability.title()}")
        render_pills(product.key_features, "No key features provided")
        st.markdown("</div>", unsafe_allow_html=True)

        with st.expander("Analytics overview", expanded=True):
            st.write(f"Queries run: {len(per_query_results)}")
            st.write(f"Queries mentioning the product: {mentioned_queries}")
            st.write(f"Best similarity score: {strongest_query_score}")
            st.write(f"Lowest similarity score: {weakest_query_score}")

        with st.expander("Missing feature coverage", expanded=True):
            render_pills(analysis["missing_features"], "No missing features detected")

        with st.expander("Recommendation brief", expanded=True):
            st.markdown(recommendations)

        with st.expander("Export report", expanded=False):
            st.write("Download the full structured report for sharing or follow-up work.")

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
