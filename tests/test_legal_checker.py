from tools.brand_intelligence.checkers.legal_checker import LegalChecker
from tools.brand_intelligence.models import CheckStatus


class FakeResponse:
    output_text = """
    {
      "matches": [
        {
          "name": "Zendora",
          "database": "EUIPO",
          "registration_number": "EU123456",
          "owner": "Example GmbH",
          "status_text": "Active",
          "goods_services": "Software and SaaS services",
          "jurisdiction": "European Union",
          "source_url": "https://example.com/trademark",
          "similarity_score": 92,
          "industry_overlap_score": 88,
          "details": "Very similar name in an overlapping software market."
        },
        {
          "name": "Cendoria",
          "database": "WIPO",
          "registration_number": null,
          "owner": null,
          "status_text": "Unknown",
          "goods_services": "Consumer goods",
          "jurisdiction": "International",
          "source_url": null,
          "similarity_score": 65,
          "industry_overlap_score": 20,
          "details": "Moderately similar name but limited industry overlap."
        }
      ],
      "summary": "One strong and one moderate potential conflict found.",
      "recommendation": "Manual legal review is recommended.",
      "sources_checked": [
        "EUIPO",
        "WIPO"
      ]
    }
    """


class FakeResponsesAPI:
    def create(self, **kwargs):
        return FakeResponse()


class FakeClient:
    def __init__(self):
        self.responses = FakeResponsesAPI()


def test_legal_checker_can_be_created():
    checker = LegalChecker()
    assert checker is not None


def test_check_name_parses_and_sorts_matches():
    checker = LegalChecker(client=FakeClient())

    result = checker.check_name(
        brand_name="Cendora",
        product_description="AI-powered IT support software",
    )

    assert result.query == "Cendora"
    assert result.status == CheckStatus.CONFLICT
    assert len(result.matches) == 2

    assert result.matches[0].name == "Zendora"
    assert result.matches[0].conflict_risk == CheckStatus.CONFLICT

    assert result.matches[1].name == "Cendoria"
    assert result.matches[1].conflict_risk == CheckStatus.CLEAR

    assert result.summary == (
        "One strong and one moderate potential conflict found."
    )
    assert result.recommendation == (
        "Manual legal review is recommended."
    )
    assert result.sources_checked == [
        "EUIPO",
        "WIPO",
    ]


def test_calculate_score_uses_highest_risk_match():
    checker = LegalChecker(client=FakeClient())

    result = checker.check_name(
        brand_name="Cendora",
        product_description="AI-powered IT support software",
    )

    score = checker.calculate_score(result)

    assert score == 0.94


def test_get_rejection_reasons_returns_only_conflicts():
    checker = LegalChecker(client=FakeClient())

    result = checker.check_name(
        brand_name="Cendora",
        product_description="AI-powered IT support software",
    )

    reasons = checker.get_rejection_reasons(result)

    assert reasons == [
        "Magas védjegykockázat: Zendora "
        "(EUIPO) – EU123456"
    ]