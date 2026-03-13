from __future__ import annotations

import html
import json
from pathlib import Path

import streamlit as st

try:
    from streamlit_echarts import st_echarts
except ImportError:  # pragma: no cover - optional dependency for richer charts
    st_echarts = None

from config import DEBUG_MODE
from core.nlp_analyzer import aggregate_results
from core.product_schema import Product
from core.query_engine import build_queries, run_all_queries
from core.recommender import generate_recommendations

PRODUCT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sample_products.json"
STYLESHEET_PATH = Path(__file__).resolve().parent / "new.css"
ROCK_CREEK_BRAND = "Rock Creek Crates"


def load_stylesheet() -> None:
    """Inject the dashboard stylesheet from disk."""
    if STYLESHEET_PATH.exists():
        st.markdown(f"<style>{STYLESHEET_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def load_demo_products() -> list[Product]:
    """Load the seeded demo products from disk."""
    with PRODUCT_DATA_PATH.open(encoding="utf-8") as file:
        raw_products = json.load(file)
    return [Product.model_validate(item) for item in raw_products]


def rock_creek_products() -> list[Product]:
    """Return only the Rock Creek Crates products for the sidebar selector."""
    return [product for product in load_demo_products() if product.brand == ROCK_CREEK_BRAND]


def h(text: str) -> str:
    """HTML-escape text for inline custom markup."""
    return html.escape(text)


def render_header() -> None:
    st.markdown(
        """
        <section class="hero-panel">
            <div class="eyebrow">North Carolina A&T State University</div>
            <h1>AISLED: AI Visibility Analyzer</h1>
            <p class="hero-copy">
                Diagnose how product pages appear in AI shopping flows, and surface missing facts.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(products: list[Product], selected_product: Product) -> bool:
    """Render the non-editable sidebar product selector."""
    with st.sidebar:
        st.markdown("## Rock Creek Crates")
        st.markdown('<div class="crate-button-list">', unsafe_allow_html=True)
        for product in products:
            button_type = "primary" if product.name == selected_product.name else "secondary"
            if st.button(
                product.name,
                key=f"crate-select-{product.name}",
                type=button_type,
                use_container_width=True,
            ):
                st.session_state["selected_product_name"] = product.name
                selected_product = product
        st.markdown("</div>", unsafe_allow_html=True)

        selected_product = next(
            product for product in products if product.name == st.session_state.get("selected_product_name", selected_product.name)
        )
        st.session_state["selected_product_name"] = selected_product.name

        st.markdown("### Product Snapshot")
        st.markdown(
            f"""
            <div class="sidebar-card">
                <div class="sidebar-card__label">{h(selected_product.category)}</div>
                <div class="sidebar-card__title">{h(selected_product.name)}</div>
                <div class="sidebar-card__meta">${selected_product.price:,.0f} · {h(selected_product.availability.title())}</div>
                <div class="sidebar-card__copy">{h(selected_product.description)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("### Key Features")
        for feature in selected_product.key_features:
            st.markdown(f"- {feature}")

        run = st.button("Analyze Visibility", type="primary", use_container_width=True)

    return run


def compute_hallucination_rate(analysis: dict[str, object]) -> float:
    per_query = analysis.get("per_query", {})
    if not per_query:
        return 0.0
    flagged = sum(1 for result in per_query.values() if result.get("hallucinated_claims"))
    return round(flagged / len(per_query) * 100, 1)


def feature_coverage(product: Product, analysis: dict[str, object]) -> list[dict[str, object]]:
    missing = set(analysis["missing_features"])
    return [
        {
            "feature": feature,
            "covered": 0 if feature in missing else 1,
        }
        for feature in product.key_features
    ]


def score_summary(product: Product, analysis: dict[str, object]) -> dict[str, float]:
    coverage = feature_coverage(product, analysis)
    covered_count = sum(item["covered"] for item in coverage)
    coverage_rate = round((covered_count / len(coverage)) * 100, 1) if coverage else 0.0
    hallucination_rate = compute_hallucination_rate(analysis)
    trust_score = max(0.0, round(100 - hallucination_rate, 1))
    return {
        "visibility": round(analysis["visibility_rate"] * 100, 1),
        "accuracy": round(analysis["avg_accuracy_score"] * 100, 1),
        "coverage": coverage_rate,
        "trust": trust_score,
    }


def render_metric_cards(product: Product, analysis: dict[str, object]) -> None:
    scores = score_summary(product, analysis)
    hallucination_rate = compute_hallucination_rate(analysis)
    missing_count = len(analysis["missing_features"])
    metric_cols = st.columns(4, gap="large")
    metric_data = [
        ("Visibility", f"{scores['visibility']:.0f}%", "Share of prompts that mention the product."),
        ("Accuracy", f"{scores['accuracy']:.0f}", "Semantic alignment with source product facts."),
        ("Feature Coverage", f"{scores['coverage']:.0f}%", "Key product details preserved in responses."),
        ("Hallucination", f"{hallucination_rate:.0f}%", f"{missing_count} missing features across the query set."),
    ]
    for column, (label, value, note) in zip(metric_cols, metric_data, strict=True):
        with column:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-card__label">{label}</div>
                    <div class="metric-card__value">{value}</div>
                    <div class="metric-card__note">{note}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_chart_panel(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="panel-heading">
            <div>
                <div class="panel-heading__title">{h(title)}</div>
                <div class="panel-heading__subtitle">{h(subtitle)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_gauge_chart(product: Product, analysis: dict[str, object]) -> None:
    scores = score_summary(product, analysis)
    render_chart_panel("Visibility Score", "Gauge view inspired by ECharts demo dashboards")
    if st_echarts:
        option = {
            "backgroundColor": "transparent",
            "series": [
                {
                    "type": "gauge",
                    "min": 0,
                    "max": 100,
                    "progress": {"show": True, "width": 18},
                    "axisLine": {"lineStyle": {"width": 18, "color": [[0.4, "#ff7b72"], [0.75, "#ffb020"], [1, "#12d5ff"]]}},
                    "axisTick": {"show": False},
                    "splitLine": {"show": False},
                    "axisLabel": {"color": "#8aa0c8"},
                    "pointer": {"show": True, "length": "68%", "width": 5},
                    "detail": {"formatter": "{value}%", "color": "#f4f7fb", "fontSize": 24, "offsetCenter": [0, "65%"]},
                    "title": {"color": "#8aa0c8", "fontSize": 12, "offsetCenter": [0, "88%"]},
                    "data": [{"value": scores["visibility"], "name": product.name}],
                }
            ],
        }
        st_echarts(options=option, height="290px")
    else:
        st.progress(scores["visibility"] / 100)
        st.metric("Visibility Score", f"{scores['visibility']:.0f}%")


def render_feature_chart(product: Product, analysis: dict[str, object]) -> None:
    coverage = feature_coverage(product, analysis)
    render_chart_panel("Feature Retention", "Covered vs missing product facts across the analysis")
    if st_echarts:
        option = {
            "backgroundColor": "transparent",
            "grid": {"left": 20, "right": 16, "top": 18, "bottom": 20, "containLabel": True},
            "xAxis": {"type": "value", "max": 1, "axisLabel": {"show": False}, "splitLine": {"lineStyle": {"color": "rgba(138,160,200,0.12)"}}},
            "yAxis": {
                "type": "category",
                "data": [item["feature"] for item in coverage],
                "axisLabel": {"color": "#dbe5f5", "fontSize": 11},
            },
            "series": [
                {
                    "type": "bar",
                    "data": [item["covered"] for item in coverage],
                    "barWidth": 18,
                    "itemStyle": {
                        "borderRadius": [0, 10, 10, 0],
                        "color": {
                            "type": "linear",
                            "x": 0,
                            "y": 0,
                            "x2": 1,
                            "y2": 0,
                            "colorStops": [{"offset": 0, "color": "#14c9ff"}, {"offset": 1, "color": "#16d69e"}],
                        },
                    },
                }
            ],
        }
        st_echarts(options=option, height="290px")
    else:
        for item in coverage:
            st.write(f"{item['feature']}: {'Covered' if item['covered'] else 'Missing'}")


def render_radar_chart(product: Product, analysis: dict[str, object]) -> None:
    scores = score_summary(product, analysis)
    render_chart_panel("Trust Radar", "Quick view of visibility, accuracy, coverage, and trust")
    if st_echarts:
        option = {
            "backgroundColor": "transparent",
            "radar": {
                "indicator": [
                    {"name": "Visibility", "max": 100},
                    {"name": "Accuracy", "max": 100},
                    {"name": "Coverage", "max": 100},
                    {"name": "Trust", "max": 100},
                ],
                "axisName": {"color": "#dbe5f5"},
                "splitArea": {"areaStyle": {"color": ["rgba(11,18,38,0.85)", "rgba(9,16,32,0.65)"]}},
                "splitLine": {"lineStyle": {"color": "rgba(138,160,200,0.2)"}},
                "axisLine": {"lineStyle": {"color": "rgba(138,160,200,0.2)"}},
            },
            "series": [
                {
                    "type": "radar",
                    "data": [
                        {
                            "value": [scores["visibility"], scores["accuracy"], scores["coverage"], scores["trust"]],
                            "name": product.name,
                            "areaStyle": {"color": "rgba(18, 213, 255, 0.24)"},
                            "lineStyle": {"color": "#12d5ff", "width": 2},
                            "symbolSize": 6,
                            "itemStyle": {"color": "#ffb020"},
                        }
                    ]
                }
            ],
        }
        st_echarts(options=option, height="290px")
    else:
        st.json(scores)


def render_selected_product(product: Product) -> None:
    features = "".join(f"<span class='pill'>{h(feature)}</span>" for feature in product.key_features)
    product_url = str(product.url) if product.url else "No product URL available"
    st.markdown(
        f"""
        <section class="product-panel">
            <div class="product-panel__eyebrow">Selected Product</div>
            <div class="product-panel__title">{h(product.name)}</div>
            <div class="product-panel__meta">{h(product.brand)} · {h(product.category)} · ${product.price:,.0f}</div>
            <div class="pill-row">{features}</div>
            <div class="product-panel__copy">{h(product.description)}</div>
            <div class="product-panel__link"><a href="{h(product_url)}" target="_blank">{h(product_url)}</a></div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_query_cards(product: Product, analysis: dict[str, object], query_results: dict[str, str]) -> None:
    comparisons = [query for query in build_queries(product) if "GUNNER G1 Kennel Black" in query]
    comparison_note = f"{len(comparisons)} comparison prompts target GUNNER G1 Kennel Black."
    st.markdown(
        f"""
        <section class="panel">
            <div class="panel-heading">
                <div>
                    <div class="panel-heading__title">Query Answer Deck</div>
                    <div class="panel-heading__subtitle">
                        Click any prompt to open a floating scrollable card with the full concatenated answer. {h(comparison_note)}
                    </div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

    prompt_cols = st.columns(2, gap="medium")
    for index, (query, result) in enumerate(analysis["per_query"].items()):
        mention = "Mentioned" if result["mentioned"] else "Not Mentioned"
        missing_features = ", ".join(result["missing_features"][:3]) or "None"
        hallucinations = ", ".join(result["hallucinated_claims"][:2]) or "None detected"
        answer_body = "\n\n".join(
            [
                f"Prompt: {query}",
                f"Mention status: {mention}",
                f"Similarity score: {result['similarity_score']}",
                f"Missing features: {missing_features}",
                f"Hallucinations: {hallucinations}",
                f"Model response: {query_results[query]}",
            ]
        )
        with prompt_cols[index % 2]:
            with st.popover(f"Prompt {index + 1}", use_container_width=True):
                st.markdown(
                    f"""
                    <div class="floating-answer-card">
                        <div class="floating-answer-card__prompt">{h(query)}</div>
                        <div class="floating-answer-card__meta">
                            <span>{h(mention)}</span>
                            <span>Similarity {result['similarity_score']}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "Concatenated answer",
                    value=answer_body,
                    height=320,
                    disabled=True,
                    key=f"query-answer-{index}",
                    label_visibility="collapsed",
                )

    st.markdown("</section>", unsafe_allow_html=True)


def render_recommendations(recommendations: str) -> None:
    st.markdown(
        """
        <section class="panel">
            <div class="panel-heading">
                <div>
                    <div class="panel-heading__title">Recommendations</div>
                    <div class="panel-heading__subtitle">Generated actions to improve visibility and reduce drift</div>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(recommendations)
    st.markdown("</section>", unsafe_allow_html=True)


st.set_page_config(page_title="AI Visibility Analyzer", layout="wide")
load_stylesheet()

products = rock_creek_products()
if not products:
    st.error("No Rock Creek Crates products were found in data/sample_products.json.")
    st.stop()

default_product = products[0]
selected_name = st.session_state.get("selected_product_name", default_product.name)
selected_product = next((product for product in products if product.name == selected_name), default_product)

render_header()

if DEBUG_MODE:
    st.info("Debug mode is enabled. Claude calls are replaced with mock responses.")

run = render_sidebar(products, selected_product)
selected_name = st.session_state.get("selected_product_name", default_product.name)
selected_product = next((product for product in products if product.name == selected_name), default_product)

render_selected_product(selected_product)

if run:
    with st.spinner("Querying AI models..."):
        query_results = run_all_queries(selected_product)
    with st.spinner("Running NLP analysis..."):
        analysis = aggregate_results(selected_product, query_results)
    with st.spinner("Generating recommendations..."):
        recommendations = generate_recommendations(selected_product, analysis)

    st.session_state["analysis_product_name"] = selected_product.name
    st.session_state["query_results"] = query_results
    st.session_state["analysis"] = analysis
    st.session_state["recommendations"] = recommendations

analysis = st.session_state.get("analysis")
query_results = st.session_state.get("query_results")
recommendations = st.session_state.get("recommendations")

if analysis and query_results and recommendations and st.session_state.get("analysis_product_name") == selected_product.name:
    render_metric_cards(selected_product, analysis)
    chart_col1, chart_col2, chart_col3 = st.columns(3, gap="large")
    with chart_col1:
        st.markdown('<section class="panel chart-panel">', unsafe_allow_html=True)
        render_gauge_chart(selected_product, analysis)
        st.markdown("</section>", unsafe_allow_html=True)
    with chart_col2:
        st.markdown('<section class="panel chart-panel">', unsafe_allow_html=True)
        render_feature_chart(selected_product, analysis)
        st.markdown("</section>", unsafe_allow_html=True)
    with chart_col3:
        st.markdown('<section class="panel chart-panel">', unsafe_allow_html=True)
        render_radar_chart(selected_product, analysis)
        st.markdown("</section>", unsafe_allow_html=True)

    render_query_cards(selected_product, analysis, query_results)
    render_recommendations(recommendations)

    export_data = {
        "product": selected_product.model_dump(mode="json"),
        "analysis": analysis,
        "recommendations": recommendations,
    }
    st.download_button(
        "Download Full Report (JSON)",
        data=json.dumps(export_data, indent=2),
        file_name=f"{selected_product.brand}_{selected_product.name}_visibility_report.json",
        mime="application/json",
        use_container_width=True,
    )
