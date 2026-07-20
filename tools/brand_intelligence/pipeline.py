from __future__ import annotations

from datetime import UTC, datetime

from tools.brand_intelligence.checkers.company_checker import (
    CompanyChecker,
)
from tools.brand_intelligence.checkers.domain_checker import (
    DomainChecker,
)
from tools.brand_intelligence.models import BrandCandidate


class BrandIntelligencePipeline:
    def __init__(
        self,
        domain_checker: DomainChecker | None = None,
        company_checker: CompanyChecker | None = None,
    ) -> None:
        self.domain_checker = (
            domain_checker or DomainChecker()
        )
        self.company_checker = (
            company_checker or CompanyChecker()
        )

    def analyze_name(
        self,
        name: str,
        product_description: str,
        target_market: str = (
            "Germany, European Union and international B2B market"
        ),
    ) -> BrandCandidate:
        candidate = BrandCandidate(name=name)

        candidate.domains = (
            self.domain_checker.check_name(name)
        )

        candidate.domain_score = (
            self.domain_checker.calculate_score(
                candidate.domains
            )
        )

        candidate.company_matches = (
            self.company_checker.check_name(
                brand_name=name,
                product_description=product_description,
                target_market=target_market,
            )
        )

        candidate.company_conflict_score = (
            self.company_checker.calculate_score(
                candidate.company_matches
            )
        )

        rejection_reasons = (
            self.company_checker.get_rejection_reasons(
                candidate.company_matches
            )
        )

        candidate.rejection_reasons.extend(
            rejection_reasons
        )

        candidate.rejected = bool(
            candidate.rejection_reasons
        )

        return candidate

    @staticmethod
    def generated_at() -> str:
        return datetime.now(UTC).isoformat()