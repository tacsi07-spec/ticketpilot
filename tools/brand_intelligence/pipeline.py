from __future__ import annotations

from datetime import UTC, datetime

from tools.brand_intelligence.checkers.domain_checker import (
    DomainChecker,
)
from tools.brand_intelligence.models import BrandCandidate


class BrandIntelligencePipeline:
    def __init__(
        self,
        domain_checker: DomainChecker | None = None,
    ) -> None:
        self.domain_checker = domain_checker or DomainChecker()

    def analyze_name(
        self,
        name: str,
    ) -> BrandCandidate:
        candidate = BrandCandidate(name=name)

        candidate.domains = self.domain_checker.check_name(name)
        candidate.domain_score = self.domain_checker.calculate_score(
            candidate.domains
        )

        return candidate

    @staticmethod
    def generated_at() -> str:
        return datetime.now(UTC).isoformat()