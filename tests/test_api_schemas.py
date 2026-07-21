import pytest
from pydantic import ValidationError

from backend.schemas.request import (
    AnalyzeRequest,
    DEFAULT_MARKET,
)


def test_analyze_request_accepts_valid_input():
    request = AnalyzeRequest(
        name="Cendora",
        product=(
            "AI-powered IT support assistant"
        ),
        market="Germany and European Union",
    )

    assert request.name == "Cendora"
    assert request.product == (
        "AI-powered IT support assistant"
    )
    assert request.market == (
        "Germany and European Union"
    )


def test_analyze_request_strips_whitespace():
    request = AnalyzeRequest(
        name="  Cendora  ",
        product=(
            "  AI-powered IT support assistant  "
        ),
        market="  Germany  ",
    )

    assert request.name == "Cendora"
    assert request.product == (
        "AI-powered IT support assistant"
    )
    assert request.market == "Germany"


def test_analyze_request_uses_default_market():
    request = AnalyzeRequest(
        name="Cendora",
        product=(
            "AI-powered IT support assistant"
        ),
    )

    assert request.market == DEFAULT_MARKET


@pytest.mark.parametrize(
    "invalid_name",
    [
        "",
        " ",
        "A",
        "---",
        "!!!",
    ],
)
def test_analyze_request_rejects_invalid_name(
    invalid_name: str,
):
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            name=invalid_name,
            product=(
                "AI-powered IT support assistant"
            ),
        )


@pytest.mark.parametrize(
    "invalid_product",
    [
        "",
        " ",
        "Software",
    ],
)
def test_analyze_request_rejects_short_product(
    invalid_product: str,
):
    with pytest.raises(ValidationError):
        AnalyzeRequest(
            name="Cendora",
            product=invalid_product,
        )