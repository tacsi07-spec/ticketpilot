from __future__ import annotations

import re
import time
import unicodedata
from dataclasses import dataclass

import requests

from .models import FinalBrandResult


RDAP_BASE_URL = "https://rdap.org/domain/"


@dataclass
class DomainResult:
    domain: str
    status: str
    available: bool | None
    bonus: float


class DomainChecker:
    """
    .ai domainek ellenőrzése RDAP segítségével.

    A possibly_available eredmény nem garantálja, hogy
    a domain ténylegesen regisztrálható.
    """

    def __init__(
        self,
        timeout: int = 20,
        delay_between_requests: float = 0.7,
    ) -> None:
        self.timeout = timeout
        self.delay_between_requests = delay_between_requests

        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/rdap+json",
                "User-Agent": (
                    "BrandFinder/2.1 "
                    "(personal domain availability research)"
                ),
            }
        )

    def close(self) -> None:
        self.session.close()

    def __enter__(self) -> DomainChecker:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        self.close()

    @staticmethod
    def normalize_name(name: str) -> str:
        """A márkanevet domain-kompatibilis formára alakítja."""

        normalized = unicodedata.normalize("NFKD", name)

        ascii_name = normalized.encode(
            "ascii",
            "ignore",
        ).decode("ascii")

        ascii_name = ascii_name.casefold()
        ascii_name = re.sub(r"[^a-z0-9-]", "", ascii_name)
        ascii_name = ascii_name.strip("-")

        if not ascii_name:
            raise ValueError(
                f"A névből nem készíthető domain: {name!r}"
            )

        return ascii_name

    def check(self, name: str) -> DomainResult:
        normalized_name = self.normalize_name(name)
        domain = f"{normalized_name}.ai"
        url = f"{RDAP_BASE_URL}{domain}"

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
            )

            if response.status_code == 404:
                return DomainResult(
                    domain=domain,
                    status="possibly_available",
                    available=True,
                    bonus=5.0,
                )

            if response.status_code == 200:
                return DomainResult(
                    domain=domain,
                    status="registered",
                    available=False,
                    bonus=-15.0,
                )

            if response.status_code == 429:
                return DomainResult(
                    domain=domain,
                    status="rate_limited",
                    available=None,
                    bonus=0.0,
                )

            return DomainResult(
                domain=domain,
                status=f"unknown_{response.status_code}",
                available=None,
                bonus=0.0,
            )

        except requests.Timeout as exc:
            print(
                f"      Időtúllépés: {domain} – {exc}",
                flush=True,
            )

            return DomainResult(
                domain=domain,
                status="timeout",
                available=None,
                bonus=0.0,
            )

        except requests.RequestException as exc:
            print(
                f"      RDAP-hiba: {domain} – "
                f"{type(exc).__name__}: {exc}",
                flush=True,
            )

            return DomainResult(
                domain=domain,
                status="request_error",
                available=None,
                bonus=0.0,
            )

    def check_results(
        self,
        results: list[FinalBrandResult],
    ) -> list[FinalBrandResult]:
        """
        Ellenőrzi a döntős neveket, hozzáadja a domainadatokat,
        majd újrarendezi a listát.
        """

        checked_results: list[FinalBrandResult] = []
        total = len(results)

        for index, result in enumerate(results, start=1):
            print(
                f"      Domain ellenőrzése "
                f"{index}/{total}: {result.name}.ai",
                flush=True,
            )

            domain_result = self.check(result.name)

            result.domain = domain_result.domain
            result.domain_status = domain_result.status
            result.domain_available = domain_result.available
            result.domain_bonus = domain_result.bonus

            result.final_score = round(
                result.final_score + domain_result.bonus,
                2,
            )

            checked_results.append(result)

            if index < total:
                time.sleep(self.delay_between_requests)

        checked_results.sort(
            key=lambda item: (
                item.domain_available is True,
                item.final_score,
            ),
            reverse=True,
        )

        return checked_results