from __future__ import annotations

import logging
import re
import time
from dataclasses import dataclass

import requests

from tools.brand_intelligence.config import (
    BrandIntelligenceConfig,
    DEFAULT_CONFIG,
)
from tools.brand_intelligence.models import (
    CheckStatus,
    DomainCheckResult,
)


LOGGER = logging.getLogger(__name__)

RDAP_BASE_URL = "https://rdap.org/domain/"


@dataclass(frozen=True)
class RawDomainResult:
    domain: str
    http_status: int | None
    response_text: str = ""
    error: str | None = None


class DomainChecker:
    def __init__(
        self,
        config: BrandIntelligenceConfig = DEFAULT_CONFIG,
    ) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.config.user_agent,
                "Accept": "application/rdap+json, application/json",
            }
        )

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized = name.strip().lower()
        normalized = re.sub(r"[^a-z0-9-]", "", normalized)
        normalized = re.sub(r"-+", "-", normalized)

        return normalized.strip("-")

    def build_domain(
        self,
        name: str,
        extension: str,
    ) -> str:
        normalized_name = self.normalize_name(name)
        normalized_extension = extension.lower().lstrip(".")

        if not normalized_name:
            raise ValueError(
                "A márkanév normalizálás után üres."
            )

        if not normalized_extension:
            raise ValueError(
                "A domainvégződés nem lehet üres."
            )

        return f"{normalized_name}.{normalized_extension}"

    def _request_domain(
        self,
        domain: str,
    ) -> RawDomainResult:
        url = f"{RDAP_BASE_URL}{domain}"

        try:
            response = self.session.get(
                url,
                timeout=self.config.domain_timeout_seconds,
            )

            return RawDomainResult(
                domain=domain,
                http_status=response.status_code,
                response_text=response.text[:500],
            )

        except requests.RequestException as exc:
            LOGGER.warning(
                "Domainellenőrzési hiba: %s – %s",
                domain,
                exc,
            )

            return RawDomainResult(
                domain=domain,
                http_status=None,
                error=str(exc),
            )

    @staticmethod
    def _interpret_result(
        result: RawDomainResult,
    ) -> DomainCheckResult:
        extension = result.domain.rsplit(".", 1)[-1]

        if result.http_status == 200:
            return DomainCheckResult(
                extension=extension,
                domain=result.domain,
                status=CheckStatus.CONFLICT,
                possibly_available=False,
                details="A domainhoz RDAP-regisztráció tartozik.",
            )

        if result.http_status == 404:
            return DomainCheckResult(
                extension=extension,
                domain=result.domain,
                status=CheckStatus.CLEAR,
                possibly_available=True,
                details=(
                    "Az RDAP nem talált regisztrációt. "
                    "A domain valószínűleg elérhető, "
                    "de ezt regisztrátornál is ellenőrizni kell."
                ),
            )

        if result.http_status in {400, 422}:
            return DomainCheckResult(
                extension=extension,
                domain=result.domain,
                status=CheckStatus.UNKNOWN,
                possibly_available=None,
                details=(
                    "Az RDAP nem tudta feldolgozni "
                    "ezt a domainvégződést."
                ),
            )

        if result.http_status == 429:
            return DomainCheckResult(
                extension=extension,
                domain=result.domain,
                status=CheckStatus.UNKNOWN,
                possibly_available=None,
                details=(
                    "Az RDAP ideiglenesen korlátozta "
                    "a kéréseket."
                ),
            )

        if result.error:
            return DomainCheckResult(
                extension=extension,
                domain=result.domain,
                status=CheckStatus.UNKNOWN,
                possibly_available=None,
                details=f"Hálózati hiba: {result.error}",
            )

        return DomainCheckResult(
            extension=extension,
            domain=result.domain,
            status=CheckStatus.UNKNOWN,
            possibly_available=None,
            details=(
                "Nem egyértelmű RDAP-válasz. "
                f"HTTP-státusz: {result.http_status}"
            ),
        )

    def check_domain(
        self,
        domain: str,
    ) -> DomainCheckResult:
        raw_result = self._request_domain(domain)
        return self._interpret_result(raw_result)

    def check_name(
        self,
        name: str,
        extensions: tuple[str, ...] | None = None,
    ) -> list[DomainCheckResult]:
        selected_extensions = (
            extensions
            if extensions is not None
            else self.config.domain_extensions
        )

        results: list[DomainCheckResult] = []

        for index, extension in enumerate(selected_extensions):
            domain = self.build_domain(
                name=name,
                extension=extension,
            )

            LOGGER.info(
                "Domain ellenőrzése: %s",
                domain,
            )

            results.append(
                self.check_domain(domain)
            )

            is_last_request = (
                index == len(selected_extensions) - 1
            )

            if not is_last_request:
                time.sleep(
                    self.config.domain_request_delay_seconds
                )

        return results

    def calculate_score(
        self,
        results: list[DomainCheckResult],
    ) -> float:
        if not results:
            return 0.0

        total_score = 0.0
        total_weight = 0.0

        for result in results:
            is_important = (
                result.extension
                in self.config.important_extensions
            )

            weight = 2.0 if is_important else 1.0

            if result.status == CheckStatus.CLEAR:
                score = self.config.available_domain_score

            elif result.status == CheckStatus.CONFLICT:
                score = self.config.registered_domain_score

            else:
                score = self.config.unknown_domain_score

            total_score += score * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return round(
            total_score / total_weight,
            2,
        )