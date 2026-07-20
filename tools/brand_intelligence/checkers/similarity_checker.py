from __future__ import annotations

import re
import unicodedata

from rapidfuzz import fuzz

from tools.brand_intelligence.models import (
    CheckStatus,
    CompanyMatch,
    SimilarityResult,
)
from tools.brand_intelligence.utils.brand_normalizer import (
    BrandNameNormalizer,
)


class SimilarityChecker:
    conflict_threshold: float = 82.0
    warning_threshold: float = 65.0

    def __init__(
        self,
        normalizer: BrandNameNormalizer | None = None,
    ) -> None:
        self.normalizer = (
            normalizer or BrandNameNormalizer()
        )

    @staticmethod
    def normalize_name(name: str) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            name.strip().lower(),
        )

        normalized = "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

        return re.sub(
            r"[^a-z0-9]",
            "",
            normalized,
        )

    @staticmethod
    def _simple_phonetic_form(name: str) -> str:
        replacements = (
            ("sch", "sh"),
            ("ph", "f"),
            ("ck", "k"),
            ("qu", "k"),
            ("c", "k"),
            ("z", "s"),
            ("v", "f"),
            ("y", "i"),
            ("x", "ks"),
        )

        phonetic = name

        for source, target in replacements:
            phonetic = phonetic.replace(
                source,
                target,
            )

        return re.sub(
            r"([a-z])\1+",
            r"\1",
            phonetic,
        )

    def _status_from_score(
        self,
        score: float,
    ) -> CheckStatus:
        if score >= self.conflict_threshold:
            return CheckStatus.CONFLICT

        if score >= self.warning_threshold:
            return CheckStatus.WARNING

        return CheckStatus.CLEAR

    def compare(
        self,
        candidate_name: str,
        compared_name: str,
    ) -> SimilarityResult:
        canonical_candidate = (
            self.normalizer.canonicalize(
                candidate_name
            )
        )

        canonical_compared = (
            self.normalizer.canonicalize(
                compared_name
            )
        )

        candidate = self.normalize_name(
            canonical_candidate
        )
        compared = self.normalize_name(
            canonical_compared
        )

        if not candidate or not compared:
            raise ValueError(
                "A nevek normalizálás után nem lehetnek üresek."
            )

        ratio_score = float(
            fuzz.ratio(
                candidate,
                compared,
            )
        )

        candidate_phonetic = self._simple_phonetic_form(
            candidate
        )
        compared_phonetic = self._simple_phonetic_form(
            compared
        )

        phonetic_score = float(
            fuzz.ratio(
                candidate_phonetic,
                compared_phonetic,
            )
        )

        prefix_score = float(
            fuzz.WRatio(
                candidate,
                compared,
            )
        )

        length_difference = abs(
            len(candidate) - len(compared)
        )

        length_penalty = min(
            15.0,
            length_difference * 3.0,
        )

        final_score = (
            ratio_score * 0.50
            + phonetic_score * 0.35
            + prefix_score * 0.15
            - length_penalty
        )

        final_score = round(
            max(
                0.0,
                min(
                    100.0,
                    final_score,
                ),
            ),
            2,
        )

        return SimilarityResult(
            candidate_name=candidate_name,
            compared_name=compared_name,
            canonical_candidate=canonical_candidate,
            canonical_compared=canonical_compared,
            normalized_candidate=candidate,
            normalized_compared=compared,
            ratio_score=round(ratio_score, 2),
            phonetic_score=round(
                phonetic_score,
                2,
            ),
            prefix_score=round(prefix_score, 2),
            final_score=final_score,
            status=self._status_from_score(
                final_score
            ),
            details=(
                f"Canonical név: "
                f"{canonical_compared}; "
                f"karakterhasonlóság: "
                f"{ratio_score:.1f}; "
                f"fonetikai hasonlóság: "
                f"{phonetic_score:.1f}; "
                f"súlyozott hasonlóság: "
                f"{prefix_score:.1f}; "
                f"hosszkülönbségi levonás: "
                f"{length_penalty:.1f}."
            ),
        )

    def analyze_company_matches(
        self,
        candidate_name: str,
        matches: list[CompanyMatch],
    ) -> list[SimilarityResult]:
        results = [
            self.compare(
                candidate_name=candidate_name,
                compared_name=match.name,
            )
            for match in matches
        ]

        return sorted(
            results,
            key=lambda result: result.final_score,
            reverse=True,
        )

    @staticmethod
    def calculate_score(
        results: list[SimilarityResult],
    ) -> float:
        if not results:
            return 10.0

        highest_similarity = max(
            result.final_score
            for result in results
        )

        return round(
            max(
                0.0,
                10.0 - highest_similarity / 10.0,
            ),
            2,
        )

    @staticmethod
    def get_rejection_reasons(
        results: list[SimilarityResult],
    ) -> list[str]:
        return [
            (
                f"Magas névhasonlósági kockázat: "
                f"{result.compared_name} "
                f"→ {result.canonical_compared} "
                f"({result.final_score:.1f}/100)"
            )
            for result in results
            if result.status == CheckStatus.CONFLICT
        ]