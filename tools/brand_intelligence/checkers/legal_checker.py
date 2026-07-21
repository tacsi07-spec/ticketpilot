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
    LegalCheckResult,
    LegalMatch,
)
from tools.brand_intelligence.services.openai_service import (
    openai_service,
)


LOGGER = logging.getLogger(__name__)


class LegalChecker:
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
You are performing preliminary trademark and legal brand-name research.

Candidate brand:
{brand_name}

Planned product:
{product_description}

Target market:
{target_market}

Search the live web for credible public trademark and legal records
related to:

1. the exact name "{brand_name}";
2. visually similar names;
3. phonetically similar names;
4. spelling variations that may create confusion.

Focus especially on:

- EUIPO;
- WIPO Global Brand Database;
- USPTO;
- German DPMA;
- active trademarks;
- pending trademark applications;
- software and SaaS;
- artificial intelligence;
- IT support;
- helpdesk and ticketing software;
- automation;
- enterprise software.

Only include findings supported by credible public sources.
Do not invent registrations, owners, status information or URLs.

Similarity score:

100 = exact or nearly exact mark;
80-99 = very strong visual or phonetic similarity;
60-79 = moderate similarity;
30-59 = weak similarity;
0-29 = negligible similarity.

Industry overlap score:

100 = same goods or services;
80-99 = strongly overlapping market;
60-79 = partially overlapping market;
30-59 = limited overlap;
0-29 = unrelated goods or services.

Return only valid JSON in this exact shape:

{{
  "matches": [
    {{
      "name": "Trademark name",
      "database": "EUIPO, WIPO, USPTO, DPMA or other source",
      "registration_number": "Registration or application number or null",
      "owner": "Owner name or null",
      "status_text": "Active, pending, expired, cancelled or unknown",
      "goods_services": "Relevant goods and services or null",
      "jurisdiction": "Country or region or null",
      "source_url": "Direct public source URL or null",
      "similarity_score": 0,
      "industry_overlap_score": 0,
      "details": "Why this may or may not create legal risk"
    }}
  ],
  "summary": "Short evidence-based summary",
  "recommendation": "Proceed, proceed with caution, or manual legal review",
  "sources_checked": [
    "List of public databases or sources actually checked"
  ]
}}

If no credible records are found, return:

{{
  "matches": [],
  "summary": "No credible matching trademark records were found.",
  "recommendation": "Manual trademark clearance is still recommended.",
  "sources_checked": []
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
                "A Legal Checker nem érvényes JSON-választ adott."
            ) from exc

        if not isinstance(parsed, dict):
            raise ValueError(
                "A Legal Checker válasza nem JSON objektum."
            )

        return parsed

    @staticmethod
    def _clamp_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0

        return max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

    @staticmethod
    def _risk_from_scores(
        similarity_score: float,
        industry_overlap_score: float,
    ) -> CheckStatus:
        combined_score = (
            similarity_score * 0.65
            + industry_overlap_score * 0.35
        )

        if combined_score >= 80:
            return CheckStatus.CONFLICT

        if combined_score >= 55:
            return CheckStatus.WARNING

        return CheckStatus.CLEAR

    def check_name(
        self,
        brand_name: str,
        product_description: str,
        target_market: str = (
            "Germany, European Union and international B2B market"
        ),
    ) -> LegalCheckResult:
        prompt = self._build_prompt(
            brand_name=brand_name,
            product_description=product_description,
            target_market=target_market,
        )

        LOGGER.info(
            "Jogi és védjegykockázat ellenőrzése: %s",
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

        matches: list[LegalMatch] = []

        for raw_match in raw_matches:
            if not isinstance(raw_match, dict):
                continue

            name = str(
                raw_match.get("name", "")
            ).strip()

            database = str(
                raw_match.get("database", "")
            ).strip()

            if not name or not database:
                continue

            similarity_score = self._clamp_score(
                raw_match.get("similarity_score", 0)
            )
            industry_overlap_score = self._clamp_score(
                raw_match.get("industry_overlap_score", 0)
            )

            matches.append(
                LegalMatch(
                    name=name,
                    database=database,
                    registration_number=raw_match.get(
                        "registration_number"
                    ),
                    owner=raw_match.get("owner"),
                    status_text=raw_match.get("status_text"),
                    goods_services=raw_match.get(
                        "goods_services"
                    ),
                    jurisdiction=raw_match.get(
                        "jurisdiction"
                    ),
                    source_url=raw_match.get("source_url"),
                    similarity_score=similarity_score,
                    industry_overlap_score=(
                        industry_overlap_score
                    ),
                    conflict_risk=self._risk_from_scores(
                        similarity_score,
                        industry_overlap_score,
                    ),
                    details=str(
                        raw_match.get("details", "")
                    ).strip(),
                )
            )

        matches.sort(
            key=lambda match: (
                match.similarity_score * 0.65
                + match.industry_overlap_score * 0.35
            ),
            reverse=True,
        )

        overall_status = CheckStatus.CLEAR

        if any(
            match.conflict_risk == CheckStatus.CONFLICT
            for match in matches
        ):
            overall_status = CheckStatus.CONFLICT
        elif any(
            match.conflict_risk == CheckStatus.WARNING
            for match in matches
        ):
            overall_status = CheckStatus.WARNING

        sources_checked = parsed.get(
            "sources_checked",
            [],
        )

        if not isinstance(sources_checked, list):
            sources_checked = []

        return LegalCheckResult(
            query=brand_name,
            status=overall_status,
            matches=matches,
            summary=str(
                parsed.get("summary", "")
            ).strip(),
            recommendation=str(
                parsed.get("recommendation", "")
            ).strip(),
            sources_checked=[
                str(source).strip()
                for source in sources_checked
                if str(source).strip()
            ],
            manual_review_required=True,
        )

    def calculate_score(
        self,
        result: LegalCheckResult,
    ) -> float:
        if not result.matches:
            return 10.0

        highest_risk = max(
            (
                match.similarity_score * 0.65
                + match.industry_overlap_score * 0.35
            )
            for match in result.matches
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
        result: LegalCheckResult,
    ) -> list[str]:
        reasons: list[str] = []

        for match in result.matches:
            if match.conflict_risk != CheckStatus.CONFLICT:
                continue

            reason = (
                f"Magas védjegykockázat: "
                f"{match.name} "
                f"({match.database})"
            )

            if match.registration_number:
                reason += (
                    f" – {match.registration_number}"
                )

            reasons.append(reason)

        return reasons