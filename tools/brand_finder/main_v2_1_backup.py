from __future__ import annotations

import csv
import sys
from pathlib import Path

from .ai_service import BrandFinderAIService
from .domain_checker import DomainChecker
from .models import FinalBrandResult


OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "brand_candidates_v2.csv"
)


def print_header() -> None:
    print("=" * 60)
    print("Brand Finder Premium v2.1")
    print("=" * 60)


def print_naming_strategy(strategy: str) -> None:
    print("\nNaming strategy")
    print("-" * 60)
    print(strategy.strip())


def domain_status_text(
    result: FinalBrandResult,
) -> str:
    if result.domain_status == "possibly_available":
        return "szabadnak tűnik"

    if result.domain_status == "registered":
        return "regisztrált"

    if result.domain_status:
        return result.domain_status

    return "nincs ellenőrizve"


def print_results(
    results: list[FinalBrandResult],
) -> None:
    print("\nFinal ranking")
    print("=" * 60)

    if not results:
        print(
            "Nem maradt olyan név, amely mindkét "
            "AI-értékelésen átment."
        )
        return

    for index, result in enumerate(results, start=1):
        print(
            f"{index:>2}. {result.name:<15} "
            f"pont: {result.final_score:>5.2f}  "
            f"{result.target_positioning}"
        )

        print(
            f"    Domain: {result.domain or '-'} "
            f"({domain_status_text(result)}, "
            f"bónusz: {result.domain_bonus:+.0f})"
        )

        print(f"    Kiejtés: {result.pronunciation}")
        print(f"    Szlogen: {result.tagline}")
        print(f"    Jelentés: {result.meaning}")
        print(f"    VC-kockázat: {result.vc_main_risk}")
        print()


def export_results(
    results: list[FinalBrandResult],
    output_file: Path = OUTPUT_FILE,
) -> None:
    fieldnames = [
        "rank",
        "name",
        "final_score",
        "domain_bonus",
        "domain",
        "domain_status",
        "domain_available",
        "target_positioning",
        "pronunciation",
        "meaning",
        "brand_story",
        "tagline",
        "logo_idea",
        "vc_score",
        "vc_reasoning",
        "vc_main_risk",
        "memorability_score",
        "enterprise_score",
        "international_score",
        "differentiation_score",
    ]

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
            delimiter=";",
        )

        writer.writeheader()

        for rank, result in enumerate(results, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "name": result.name,
                    "final_score": result.final_score,
                    "domain_bonus": result.domain_bonus,
                    "domain": result.domain or "",
                    "domain_status": (
                        result.domain_status or ""
                    ),
                    "domain_available": (
                        ""
                        if result.domain_available is None
                        else result.domain_available
                    ),
                    "target_positioning": (
                        result.target_positioning
                    ),
                    "pronunciation": result.pronunciation,
                    "meaning": result.meaning,
                    "brand_story": result.brand_story,
                    "tagline": result.tagline,
                    "logo_idea": result.logo_idea,
                    "vc_score": result.vc_score,
                    "vc_reasoning": result.vc_reasoning,
                    "vc_main_risk": result.vc_main_risk,
                    "memorability_score": (
                        result.memorability_score
                    ),
                    "enterprise_score": (
                        result.enterprise_score
                    ),
                    "international_score": (
                        result.international_score
                    ),
                    "differentiation_score": (
                        result.differentiation_score
                    ),
                }
            )


def main() -> int:
    print_header()

    try:
        service = BrandFinderAIService()

        (
            generation_result,
            _vc_result,
            _marketing_result,
            final_results,
        ) = service.run_ai_workflow()

        print_naming_strategy(
            generation_result.naming_strategy
        )

        if final_results:
            print(
                "\n[4/4] Domain Checker: "
                ".ai domainek ellenőrzése...",
                flush=True,
            )

            with DomainChecker() as domain_checker:
                final_results = (
                    domain_checker.check_results(
                        final_results
                    )
                )

        print_results(final_results)
        export_results(final_results)

        print("=" * 60)
        print(f"CSV elkészült: {OUTPUT_FILE}")
        print("=" * 60)

        print(
            "\nMegjegyzés: a 'possibly_available' státuszt "
            "mindig ellenőrizd domainregisztrátornál is."
        )

        return 0

    except KeyboardInterrupt:
        print("\nA futtatást megszakítottad.")
        return 130

    except Exception as exc:
        print("\nHIBA")
        print("-" * 60)
        print(str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())