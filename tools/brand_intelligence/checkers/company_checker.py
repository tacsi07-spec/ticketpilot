from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import OpenAI

from tools.brand_intelligence.config import (
    BrandIntelligenceConfig,
    DEFAULT_CONFIG,
)
from tools.brand_intelligence.models import (
    CheckStatus,
    CompanyMatch,
)
from tools.brand_intelligence.services.openai_service import (
    openai_service,
)


LOGGER = logging.getLogger(__name__)


class CompanyChecker:
    def __init__(
        self,
        config: BrandIntelligenceConfig = DEFAULT_CONFIG,
        client: OpenAI | None = None,
    ) -> None:
        self.config = config
        self.client = client

    def _get_client(self) -> OpenAI:
        if self.client is not None:
            return self.client

        return openai_service.client

    def _build_prompt(
        self,
        brand_name: str,
        product_description: str,
        target_market: str,
    ) -> str:
        return f"""
You are performing preliminary brand-name due diligence.

Candidate brand:
{brand_name}

Planned product:
{product_description}

Target market:
{target_market}

Search the live web for active businesses, software products,
startups, SaaS platforms, AI companies, agencies and technology
projects using:

1. the exact name "{brand_name}";
2. visually or phonetically similar names;
3. spelling variations that may cause confusion.

Focus especially on:

- AI;
- SaaS;
- IT support;
- helpdesk software;
- ticketing systems;
- automation;
- CRM;
- enterprise software;
- technology consulting;
- Germany and the European Union;
- companies serving international customers.

Only include real findings supported by web search results.
Do not invent companies.

Similarity score meaning:

100 = exact same name and overlapping industry;
80-99 = nearly identical name with strong industry overlap;
60-79 = similar name or moderate industry overlap;
30-59 = weak similarity or unrelated industry;
0-29 = negligible risk.

Return only valid JSON in this exact shape:

{{
  "matches": [
    {{
      "name": "Company or product name",
      "website": "https://example.com or null",
      "industry": "Short industry description or null",
      "country": "Country or null",
      "similarity_score": 0,
      "details": "Why this may or may not conflict"
    }}
  ]
}}

Return at most {self.config.company_search_max_results} matches.
If nothing credible is found, return:

{{
  "matches": []
}}
""".strip()

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(
                r"^```(?:json)?\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
            cleaned = re.sub(
                r"\s*```$",
                "",
                cleaned,
            )

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                "A Company Checker nem érvényes JSON-választ adott."
            ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(
                "A Company Checker válasza nem JSON objektum."
            )

        return parsed

    def _risk_from_score(
        self,
        score: float,
    ) -> CheckStatus:
        if score >= self.config.company_conflict_threshold:
            return CheckStatus.CONFLICT

        if score >= self.config.company_warning_threshold:
            return CheckStatus.WARNING

        return CheckStatus.CLEAR

    def check_name(
        self,
        brand_name: str,
        product_description: str,
        target_market: str = (
            "Germany, European Union and international B2B market"
        ),
    ) -> list[CompanyMatch]:
        prompt = self._build_prompt(
            brand_name=brand_name,
            product_description=product_description,
            target_market=target_market,
        )

        LOGGER.info(
            "Cégnévütközések webes ellenőrzése: %s",
            brand_name,
        )

        client = self._get_client()

        response = client.responses.create(
            model=self.config.company_search_model,
            tools=[
                {
                    "type": "web_search",
                    "search_context_size": (
                        self.config.company_search_context_size
                    ),
                }
            ],
            input=prompt,
        )

        parsed = self._extract_json(response.output_text)
        raw_matches = parsed.get("matches", [])

        if not isinstance(raw_matches, list):
            raise ValueError(
                "A 'matches' mezőnek listának kell lennie."
            )

        results: list[CompanyMatch] = []

        for raw_match in raw_matches:
            if not isinstance(raw_match, dict):
                continue

            name = str(
                raw_match.get("name", "")
            ).strip()

            if not name:
                continue

            try:
                similarity_score = float(
                    raw_match.get(
                        "similarity_score",
                        0,
                    )
                )
            except (TypeError, ValueError):
                similarity_score = 0.0

            similarity_score = max(
                0.0,
                min(
                    100.0,
                    similarity_score,
                ),
            )

            results.append(
                CompanyMatch(
                    name=name,
                    website=raw_match.get("website"),
                    industry=raw_match.get("industry"),
                    country=raw_match.get("country"),
                    similarity_score=similarity_score,
                    conflict_risk=self._risk_from_score(
                        similarity_score
                    ),
                    details=str(
                        raw_match.get(
                            "details",
                            "",
                        )
                    ).strip(),
                )
            )

        return sorted(
            results,
            key=lambda match: match.similarity_score,
            reverse=True,
        )

    def calculate_score(
        self,
        matches: list[CompanyMatch],
    ) -> float:
        if not matches:
            return 10.0

        highest_risk = max(
            match.similarity_score
            for match in matches
        )

        score = 10.0 - (
            highest_risk / 10.0
        )

        return round(
            max(
                0.0,
                min(
                    10.0,
                    score,
                ),
            ),
            2,
        )

    def get_rejection_reasons(
        self,
        matches: list[CompanyMatch],
    ) -> list[str]:
        reasons: list[str] = []

        for match in matches:
            if match.conflict_risk != CheckStatus.CONFLICT:
                continue

            reason = (
                f"Magas cégnévütközési kockázat: "
                f"{match.name} "
                f"({match.similarity_score:.0f}/100)"
            )

            if match.website:
                reason += f" – {match.website}"

            reasons.append(reason)

        return reasons