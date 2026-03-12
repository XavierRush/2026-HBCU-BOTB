from core.product_schema import Product
from core.debug_mode import mock_query_response, mock_recommendations


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
