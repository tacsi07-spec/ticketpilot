import pytest

from tools.brand_intelligence.models import BrandCandidate
from tools.brand_intelligence.pipeline import (
    BrandIntelligencePipeline,
)


def test_calculate_final_score():
    candidate = BrandCandidate(
        name="Testbrand",
        domain_score=8.0,
        company_conflict_score=6.0,
        similarity_score=7.0,
        trademark_score=5.0,
    )

    score = (
        BrandIntelligencePipeline
        ._calculate_final_score(candidate)
    )

    assert score == pytest.approx(6.25)