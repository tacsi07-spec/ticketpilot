from pathlib import Path

from tools.brand_intelligence.models import (
    BrandCandidate,
    CheckStatus,
    CompanyMatch,
    DomainCheckResult,
    LegalCheckResult,
    LegalMatch,
    SimilarityResult,
)
from tools.brand_intelligence.report_generator import (
    HtmlReportGenerator,
)


def build_demo_candidate() -> BrandCandidate:
    return BrandCandidate(
        name="Cendora",
        final_score=7.82,
        domain_score=8.5,
        company_conflict_score=7.1,
        similarity_score=6.4,
        trademark_score=5.9,
        rejected=True,
        rejection_reasons=[
            (
                "Magas védjegykockázat: Zendora "
                "(EUIPO) – EU123456"
            )
        ],
        domains=[
            DomainCheckResult(
                extension=".ai",
                domain="cendora.ai",
                status=CheckStatus.CLEAR,
                possibly_available=True,
                details="The domain appears to be available.",
            ),
            DomainCheckResult(
                extension=".com",
                domain="cendora.com",
                status=CheckStatus.WARNING,
                possibly_available=False,
                details="The domain appears to be registered.",
            ),
        ],
        company_matches=[
            CompanyMatch(
                name="Cendora Consulting",
                website="https://example.com",
                industry="Technology consulting",
                country="Germany",
                similarity_score=68,
                conflict_risk=CheckStatus.WARNING,
                details=(
                    "Similar name, but only partial industry overlap."
                ),
            )
        ],
        similarity_results=[
            SimilarityResult(
                candidate_name="Cendora",
                compared_name="Zendora",
                canonical_candidate="cendora",
                canonical_compared="zendora",
                normalized_candidate="cendora",
                normalized_compared="zendora",
                ratio_score=86,
                phonetic_score=94,
                prefix_score=70,
                final_score=89,
                status=CheckStatus.CONFLICT,
                details=(
                    "The names are strongly similar phonetically."
                ),
            )
        ],
        legal_results=[
            LegalCheckResult(
                query="Cendora",
                status=CheckStatus.CONFLICT,
                summary=(
                    "A highly similar active software trademark "
                    "was identified."
                ),
                recommendation=(
                    "Manual legal review is recommended "
                    "before commercial use."
                ),
                sources_checked=[
                    "EUIPO",
                    "WIPO",
                ],
                matches=[
                    LegalMatch(
                        name="Zendora",
                        database="EUIPO",
                        registration_number="EU123456",
                        owner="Example Software GmbH",
                        status_text="Active",
                        goods_services=(
                            "Software, SaaS and IT services"
                        ),
                        jurisdiction="European Union",
                        source_url=(
                            "https://example.com/trademark"
                        ),
                        similarity_score=92,
                        industry_overlap_score=88,
                        conflict_risk=CheckStatus.CONFLICT,
                        details=(
                            "Strong similarity and overlapping services."
                        ),
                    )
                ],
            )
        ],
    )


def test_report_generator_renders_candidate():
    candidate = build_demo_candidate()
    generator = HtmlReportGenerator()

    html = generator.render(candidate)

    assert "<!DOCTYPE html>" in html
    assert "Cendora" in html
    assert "cendora.ai" in html
    assert "Cendora Consulting" in html
    assert "Zendora" in html
    assert "EU123456" in html
    assert "Not recommended without further review" in html


def test_report_generator_saves_html(tmp_path: Path):
    candidate = build_demo_candidate()
    generator = HtmlReportGenerator()

    output_path = tmp_path / "cendora_report.html"

    saved_path = generator.save(
        candidate=candidate,
        output_path=output_path,
    )

    assert saved_path.exists()
    assert saved_path.suffix == ".html"

    html = saved_path.read_text(
        encoding="utf-8",
    )

    assert "Brand Intelligence Report" in html
    assert "Cendora" in html