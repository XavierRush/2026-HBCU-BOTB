from __future__ import annotations

import json
from statistics import mean

import streamlit as st

from config import DEBUG_MODE
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import run_all_queries
from core.recommender import generate_recommendations

st.set_page_config(page_title="AISLED", layout="wide")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg-1: #060918;
            --bg-2: #081026;
            --surface: rgba(26, 35, 54, 0.65);
            --surface-strong: rgba(24, 32, 51, 0.88);
            --border: rgba(88, 168, 242, 0.22);
            --text: rgba(230, 239, 255, 0.92);
            --muted: rgba(197, 210, 232, 0.55);
            --accent: #18d0ff;
            --accent2: #78ffa3;
            --warn: #ff9f40;
            --danger: #ff4d6d;
            --shadow: 0 18px 48px rgba(0, 0, 0, 0.35);
        }

        html, body, .stApp {
            height: 100%;
        }

        .stApp {
            background: radial-gradient(circle at top left, rgba(5, 134, 255, 0.18), transparent 45%),
                        radial-gradient(circle at bottom right, rgba(152, 255, 181, 0.12), transparent 50%),
                        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-2) 100%);
            color: var(--text);
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        }

        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image:
                repeating-linear-gradient(0deg, rgba(255,255,255,0.05) 0 1px, transparent 1px 40px),
                repeating-linear-gradient(90deg, rgba(255,255,255,0.04) 0 1px, transparent 1px 40px);
            pointer-events: none;
            z-index: 0;
        }

        .block-container {
            padding-top: 2.5rem;
            padding-bottom: 2.5rem;
            max-width: 1400px;
        }

        .stApp,
        .stApp p,
        .stApp label,
        .stApp span,
        .stApp li,
        .stApp div,
        .stMarkdown,
        .stText,
        .stCaption {
            color: var(--text);
        }

        .stApp a {
            color: var(--accent);
            text-decoration: underline 1px rgba(24, 208, 255, 0.6);
        }

        [data-testid="stHeader"] {
            background: rgba(6, 8, 24, 0.85);
            border-bottom: 1px solid rgba(88, 168, 242, 0.18);
        }

        [data-testid="stHeader"] *,
        [data-testid="stToolbar"] *,
        [data-testid="stDecoration"] * {
            color: var(--text) !important;
            fill: var(--text) !important;
        }

        [data-testid="stToolbar"] button,
        [data-testid="stHeader"] button,
        [data-testid="stToolbar"] svg,
        [data-testid="stHeader"] svg {
            color: var(--text) !important;
            fill: var(--text) !important;
            stroke: var(--text) !important;
        }

        [data-testid="stSidebar"] {
            background: rgba(6, 9, 24, 0.92);
            border-right: 1px solid rgba(88, 168, 242, 0.18);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
            color: var(--text) !important;
        }

        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stTextArea textarea,
        [data-testid="stSidebar"] .stNumberInput input,
        [data-testid="stSidebar"] div[data-baseweb="select"] > div,
        [data-testid="stSidebar"] div[data-baseweb="base-input"] > div {
            background: rgba(18, 24, 44, 0.76);
            color: var(--text) !important;
            border: 1px solid rgba(88, 168, 242, 0.22);
        }

        [data-testid="stSidebar"] input::placeholder,
        [data-testid="stSidebar"] textarea::placeholder {
            color: rgba(230, 239, 255, 0.5) !important;
        }

        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] .stMarkdown,
        [data-testid="stSidebar"] .stSelectbox div,
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] input,
        [data-testid="stSidebar"] button,
        [data-testid="stSidebar"] svg {
            color: var(--text) !important;
            fill: var(--text) !important;
            stroke: var(--text) !important;
        }

        .hero-card,
        .metric-card,
        .section-card,
        .query-card {
            border: 1px solid var(--border);
            border-radius: 22px;
            background: var(--surface);
            box-shadow: var(--shadow);
            backdrop-filter: blur(18px);
        }

        [data-testid="stExpander"],
        [data-testid="stAlert"],
        [data-testid="stDownloadButton"] > button,
        .stButton > button,
        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        .stSelectbox select,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div {
            color: var(--text);
        }

        .stTextInput input,
        .stTextArea textarea,
        .stNumberInput input,
        div[data-baseweb="select"] > div,
        div[data-baseweb="base-input"] > div {
            background: rgba(12, 17, 33, 0.9);
            border: 1px solid rgba(88, 168, 242, 0.22);
        }

        .stTextInput label,
        .stTextArea label,
        .stNumberInput label,
        .stSelectbox label,
        .stDownloadButton,
        .stCheckbox label,
        .stRadio label {
            color: var(--text) !important;
            font-weight: 600;
        }

        .stButton > button,
        .stDownloadButton > button {
            background: linear-gradient(90deg, rgba(24,208,255,0.95), rgba(120,255,163,0.85));
            color: rgba(6, 8, 24, 0.95);
            border: 1px solid rgba(24, 208, 255, 0.4);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            background: linear-gradient(90deg, rgba(24,208,255,1), rgba(120,255,163,0.95));
        }

        [data-testid="stExpander"] summary,
        [data-testid="stExpander"] summary * {
            color: var(--text) !important;
        }

        [data-testid="stAlert"] * {
            color: inherit;
        }

        .hero-card {
            padding: 1.7rem 1.6rem;
            margin-bottom: 1.4rem;
            border-radius: 28px;
        }

        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.72rem;
            color: rgba(24, 208, 255, 0.85);
            font-weight: 700;
        }

        .hero-title {
            font-size: 2.9rem;
            line-height: 1.05;
            margin: 0.35rem 0 0.45rem;
            color: rgba(240, 250, 255, 0.96);
            font-weight: 800;
        }

        .hero-copy {
            color: rgba(197, 210, 232, 0.72);
            max-width: 52rem;
            font-size: 1.05rem;
        }

        .metric-card {
            padding: 1.1rem 1.2rem;
            min-height: 160px;
            border-radius: 22px;
        }

        .metric-label {
            color: rgba(197, 210, 232, 0.55);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.09em;
            font-weight: 700;
        }

        .metric-value {
            font-size: 2.2rem;
            line-height: 1;
            font-weight: 800;
            color: rgba(240, 250, 255, 0.96);
            margin: 0.4rem 0 0.55rem;
        }

        .metric-note {
            color: rgba(197, 210, 232, 0.65);
            font-size: 0.95rem;
        }

        .section-card {
            padding: 1.2rem 1.3rem;
            margin-top: 1.1rem;
            border-radius: 24px;
        }

        .section-title {
            font-size: 1.25rem;
            font-weight: 800;
            color: rgba(240, 250, 255, 0.96);
            margin-bottom: 0.35rem;
        }

        .section-copy {
            color: rgba(197, 210, 232, 0.68);
            font-size: 0.98rem;
            margin-bottom: 0.8rem;
        }

        .pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.6rem;
        }

        .pill {
            background: rgba(24, 208, 255, 0.12);
            color: rgba(24, 208, 255, 0.92);
            border: 1px solid rgba(24, 208, 255, 0.25);
            border-radius: 999px;
            padding: 0.32rem 0.72rem;
            font-size: 0.82rem;
            font-weight: 700;
        }

        .query-card {
            padding: 1rem 1.1rem;
            margin-bottom: 0.9rem;
            border-radius: 20px;
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
            color: rgba(240, 250, 255, 0.96);
            font-size: 1.02rem;
        }

        .query-badge {
            border-radius: 999px;
            padding: 0.3rem 0.75rem;
            font-size: 0.8rem;
            font-weight: 700;
            white-space: nowrap;
            letter-spacing: 0.04em;
        }

        .query-badge.good {
            background: rgba(120, 255, 163, 0.14);
            color: rgba(120, 255, 163, 0.95);
        }

        .query-badge.warn {
            background: rgba(255, 159, 64, 0.18);
            color: rgba(255, 159, 64, 0.92);
        }

        .query-meta {
            color: rgba(197, 210, 232, 0.6);
            font-size: 0.92rem;
        }

        .stExpander {
            border: 1px solid rgba(88, 168, 242, 0.18);
            border-radius: 20px;
            background: rgba(12, 17, 33, 0.82);
        }

        code {
            color: rgba(24, 208, 255, 0.92);
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
        <div class="hero-eyebrow">Client Dashboard</div>
        <div class="hero-title">AISLED</div>
        <div class="hero-copy">
            Diagnose how AI assistants describe your product, spot missing details quickly,
            and review structured recommendations in expandable sections.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.header("Enter Your Product")
    name = st.text_input("Product Name", "Collapsible Dog Crate")
    brand = st.text_input("Brand", "Rock Creek Crates")
    category = st.text_input("Category", "dog crate")
    price = st.number_input("Price ($)", value=650.00)
    features_raw = st.text_area(
        "Key Features (one per line)",
        "Comes with 10 year warranty\nEasy to Carry Handles\nStackable Corner Guards\nUltra-Tough Overbuilt Door\n6 Durable Textured Colors\nSecondary Butterfly Latches\nUpgraded Lockable Paddle Latch\nSide Panel Screws for Added Structural Support\nOptimal Hexagon Ventilation",
    )
    description = st.text_area(
        "Product Description",
        "Rock Creek Crates’ collapsible dog crate is built for pet lovers who want a rugged yet portable home for their pup. "
        "It includes a 10-year warranty, multiple locking points, and ventilation designed to keep dogs comfortable. "
        "(293 reviews)",
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
