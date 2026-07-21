import pytest

from tools.brand_intelligence.utils.brand_normalizer import (
    BrandNameNormalizer,
)


@pytest.fixture
def normalizer() -> BrandNameNormalizer:
    return BrandNameNormalizer()


def test_removes_legal_suffix(
    normalizer: BrandNameNormalizer,
) -> None:
    assert normalizer.canonicalize("Cendora GmbH") == "Cendora"


def test_removes_multiple_suffixes(
    normalizer: BrandNameNormalizer,
) -> None:
    assert (
        normalizer.canonicalize("Cendora Company Limited")
        == "Cendora"
    )


def test_removes_domain_suffix(
    normalizer: BrandNameNormalizer,
) -> None:
    assert normalizer.canonicalize("Cendora.ai") == "Cendora"


def test_extracts_primary_name_before_separator(
    normalizer: BrandNameNormalizer,
) -> None:
    assert (
        normalizer.canonicalize("Cendora.dev / CFO Review")
        == "Cendora"
    )


def test_removes_parenthetical_content(
    normalizer: BrandNameNormalizer,
) -> None:
    assert (
        normalizer.canonicalize("CFO Review (cendora.dev)")
        == "CFO Review"
    )


def test_removes_accents(
    normalizer: BrandNameNormalizer,
) -> None:
    assert (
        normalizer.canonicalize("Árvíztűrő Kft")
        == "Arvizturo"
    )


def test_replaces_hyphens_with_spaces(
    normalizer: BrandNameNormalizer,
) -> None:
    assert (
        normalizer.canonicalize("Nova-Works Solutions")
        == "Nova Works"
    )


@pytest.mark.parametrize(
    "value",
    [
        "",
        " ",
        "   ",
    ],
)
def test_rejects_empty_name(
    normalizer: BrandNameNormalizer,
    value: str,
) -> None:
    with pytest.raises(ValueError):
        normalizer.canonicalize(value)
