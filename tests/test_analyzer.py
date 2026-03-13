from core.product_schema import Product
from core.debug_mode import mock_query_response, mock_recommendations
from core.query_engine import build_queries


def test_product_schema_accepts_required_fields():
    product = Product(
        name="MechPro K75 Keyboard",
        category="gaming keyboard",
        brand="MechPro",
        price=89.99,
        key_features=["mechanical switches", "RGB backlight"],
        description="Mechanical keyboard with RGB backlight.",
        availability="in stock",
    )

    assert product.name == "MechPro K75 Keyboard"
    assert product.availability == "in stock"


def test_mock_query_response_mentions_brand_and_name():
    product = Product(
        name="MechPro K75 Keyboard",
        category="gaming keyboard",
        brand="MechPro",
        price=89.99,
        key_features=["mechanical switches", "RGB backlight"],
        description="Mechanical keyboard with RGB backlight.",
        availability="in stock",
    )

    response = mock_query_response(product, "Is MechPro K75 Keyboard a good choice?")

    assert "MechPro" in response
    assert "K75" in response


def test_mock_recommendations_returns_visibility_guidance():
    product = Product(
        name="MechPro K75 Keyboard",
        category="gaming keyboard",
        brand="MechPro",
        price=89.99,
        key_features=["mechanical switches", "RGB backlight"],
        description="Mechanical keyboard with RGB backlight.",
        availability="in stock",
    )

    analysis = {
        "missing_features": ["RGB backlight"],
    }

    recommendations = mock_recommendations(product, analysis)

    assert "Visibility Fixes" in recommendations
    assert "RGB backlight" in recommendations


def test_build_queries_compares_rock_creek_to_gunner():
    product = Product(
        name="Collapsible Dog Crate",
        category="collapsible dog crate",
        brand="Rock Creek Crates",
        price=650.0,
        key_features=["collapsible design", "powder-coated aluminum"],
        description="Durable collapsible crate.",
        availability="in stock",
    )

    queries = build_queries(product)

    comparison_queries = [query for query in queries if "GUNNER G1 Kennel Black" in query]

    assert len(queries) == 6
    assert len(comparison_queries) == 2
