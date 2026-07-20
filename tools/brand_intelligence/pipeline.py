from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Literal

from tools.brand_intelligence.checkers.company_checker import (
    CompanyChecker,
)
from tools.brand_intelligence.checkers.domain_checker import (
    DomainChecker,
)
from tools.brand_intelligence.checkers.similarity_checker import (
    SimilarityChecker,
)
from tools.brand_intelligence.models import (
    BrandCandidate,
    CompanyMatch,
)
from tools.brand_intelligence.utils.company_cache import (
    CompanySearchCache,
)


LOGGER = logging.getLogger(__name__)

CacheStatus = Literal[
    "disabled",
    "hit",
    "miss",
    "refreshed",
]


class BrandIntelligencePipeline:
    def __init__(
        self,
        domain_checker: DomainChecker | None = None,
        company_checker: CompanyChecker | None = None,
        similarity_checker: SimilarityChecker | None = None,
        company_cache: CompanySearchCache | None = None,
    ) -> None:
        self.domain_checker = (
            domain_checker or DomainChecker()
        )

        self.company_checker = (
            company_checker or CompanyChecker()
        )

        self.similarity_checker = (
            similarity_checker or SimilarityChecker()
        )

        self.company_cache = (
            company_cache or CompanySearchCache()
        )

        self.last_company_cache_status: CacheStatus = (
            "disabled"
        )

    def _get_company_matches(
        self,
        name: str,
        product_description: str,
        target_market: str,
        use_company_cache: bool,
        refresh_company_cache: bool,
    ) -> list[CompanyMatch]:
        if not use_company_cache:
            self.last_company_cache_status = "disabled"

            LOGGER.info(
                "Company cache kikapcsolva: %s",
                name,
            )

            return self.company_checker.check_name(
                brand_name=name,
                product_description=product_description,
                target_market=target_market,
            )

        if not refresh_company_cache:
            cached_matches = self.company_cache.load(
                brand_name=name,
                product_description=product_description,
                market=target_market,
            )

            if cached_matches is not None:
                self.last_company_cache_status = "hit"

                LOGGER.info(
                    "Company cache HIT: %s",
                    name,
                )

                return cached_matches

        if refresh_company_cache:
            self.last_company_cache_status = "refreshed"

            LOGGER.info(
                "Company cache frissítése: %s",
                name,
            )
        else:
            self.last_company_cache_status = "miss"

            LOGGER.info(
                "Company cache MISS: %s",
                name,
            )

        matches = self.company_checker.check_name(
            brand_name=name,
            product_description=product_description,
            target_market=target_market,
        )

        cache_path = self.company_cache.save(
            brand_name=name,
            product_description=product_description,
            market=target_market,
            matches=matches,
        )

        LOGGER.info(
            "Company cache elmentve: %s",
            cache_path,
        )

        return matches

    def analyze_name(
        self,
        name: str,
        product_description: str,
        target_market: str = (
            "Germany, European Union and "
            "international B2B market"
        ),
        use_company_cache: bool = True,
        refresh_company_cache: bool = False,
    ) -> BrandCandidate:
        if refresh_company_cache and not use_company_cache:
            raise ValueError(
                "A company cache nem frissíthető, "
                "ha a cache használata ki van kapcsolva."
            )

        candidate = BrandCandidate(
            name=name,
        )

        candidate.domains = (
            self.domain_checker.check_name(name)
        )

        candidate.domain_score = (
            self.domain_checker.calculate_score(
                candidate.domains
            )
        )

        candidate.company_matches = (
            self._get_company_matches(
                name=name,
                product_description=product_description,
                target_market=target_market,
                use_company_cache=use_company_cache,
                refresh_company_cache=(
                    refresh_company_cache
                ),
            )
        )

        candidate.company_conflict_score = (
            self.company_checker.calculate_score(
                candidate.company_matches
            )
        )

        candidate.similarity_results = (
            self.similarity_checker
            .analyze_company_matches(
                candidate_name=name,
                matches=candidate.company_matches,
            )
        )

        candidate.similarity_score = (
            self.similarity_checker.calculate_score(
                candidate.similarity_results
            )
        )

        candidate.rejection_reasons.extend(
            self.company_checker
            .get_rejection_reasons(
                candidate.company_matches
            )
        )

        candidate.rejection_reasons.extend(
            self.similarity_checker
            .get_rejection_reasons(
                candidate.similarity_results
            )
        )

        candidate.rejection_reasons = list(
            dict.fromkeys(
                candidate.rejection_reasons
            )
        )

        candidate.rejected = bool(
            candidate.rejection_reasons
        )

        return candidate

    @staticmethod
    def generated_at() -> str:
        return datetime.now(UTC).isoformat()