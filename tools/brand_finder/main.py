from __future__ import annotations

import csv
import sys
from pathlib import Path

from .ai_service import BrandFinderAIService
from .domain_checker import DomainChecker
from .models import FinalBrandResult


MIN_AVAILABLE_DOMAINS = 3
MAX_GENERATION_ROUNDS = 5

OUTPUT_FILE = (
    Path(__file__).resolve().parent
    / "brand_candidates_v2_2.csv"
)

ALL_RESULTS_FILE = (
    Path(__file__).resolve().parent
    / "brand_candidates_v2_2_all.csv"
)


def print_header() -> None:
    print("=" * 68)
    print("Brand Finder Premium v2.2")
    print("=" * 68)
    print(
        f"Cél: legalább {MIN_AVAILABLE_DOMAINS} erős, "
        "szabadnak tűnő .ai domain"
    )
    print(
        f"Maximális generálási körök száma: "
        f"{MAX_GENERATION_ROUNDS}"
    )


def domain_status_text(
    result: FinalBrandResult,
) -> str:
    if result.domain_status == "possibly_available":
        return "szabadnak tűnik"

    if result.domain_status == "registered":
        return "regisztrált"

    if result.domain_status == "rate_limited":
        return "lekérési korlát"

    if result.domain_status == "timeout":
        return "időtúllépés"

    if result.domain_status == "request_error":
        return "kapcsolati hiba"

    return result.domain_status or "nincs ellenőrizve"


def unique_results(
    results: list[FinalBrandResult],
) -> list[FinalBrandResult]:
    """
    Eltávolítja az ismétlődő márkaneveket.

    Ha ugyanaz a név többször is megjelenik,
    a magasabb pontszámú változat marad meg.
    """
    unique_by_name: dict[str, FinalBrandResult] = {}

    for result in results:
        normalized_name = result.name.strip().casefold()

        previous = unique_by_name.get(normalized_name)

        if (
            previous is None
            or result.final_score > previous.final_score
        ):
            unique_by_name[normalized_name] = result

    return list(unique_by_name.values())


def available_results(
    results: list[FinalBrandResult],
) -> list[FinalBrandResult]:
    available = [
        result
        for result in results
        if result.domain_available is True
    ]

    available.sort(
        key=lambda result: result.final_score,
        reverse=True,
    )

    return available


def print_round_summary(
    round_number: int,
    round_results: list[FinalBrandResult],
    all_results: list[FinalBrandResult],
) -> None:
    available_this_round = available_results(round_results)
    available_total = available_results(all_results)

    print("\n" + "-" * 68)
    print(f"{round_number}. kör összesítése")
    print("-" * 68)

    print(
        f"Döntős nevek ebben a körben: "
        f"{len(round_results)}"
    )
    print(
        f"Szabadnak tűnő domainek ebben a körben: "
        f"{len(available_this_round)}"
    )
    print(
        f"Eddigi egyedi döntős nevek: "
        f"{len(all_results)}"
    )
    print(
        f"Eddigi szabadnak tűnő domainek: "
        f"{len(available_total)}/"
        f"{MIN_AVAILABLE_DOMAINS}"
    )

    if available_this_round:
        print("\nEbben a körben talált domainek:")

        for result in available_this_round:
            print(
                f"  + {result.domain} "
                f"({result.final_score:.2f} pont)"
            )


def print_results(
    results: list[FinalBrandResult],
) -> None:
    print("\n")
    print("=" * 68)
    print("FINAL RANKING – SZABADNAK TŰNŐ .AI DOMAINEK")
    print("=" * 68)

    if not results:
        print(
            "A megadott számú kör alatt nem találtunk "
            "szabadnak tűnő .ai domaint."
        )
        return

    for index, result in enumerate(results, start=1):
        print(
            f"{index:>2}. {result.name:<16} "
            f"pont: {result.final_score:>6.2f}"
        )

        print(
            f"    Domain: {result.domain or '-'} "
            f"({domain_status_text(result)}, "
            f"bónusz: {result.domain_bonus:+.0f})"
        )

        print(
            f"    Pozicionálás: "
            f"{result.target_positioning}"
        )
        print(f"    Kiejtés: {result.pronunciation}")
        print(f"    Szlogen: {result.tagline}")
        print(f"    Jelentés: {result.meaning}")
        print(f"    VC-kockázat: {result.vc_main_risk}")
        print()


def result_to_row(
    result: FinalBrandResult,
    rank: int,
) -> dict[str, object]:
    return {
        "rank": rank,
        "name": result.name,
        "final_score": result.final_score,
        "domain_bonus": result.domain_bonus,
        "domain": result.domain or "",
        "domain_status": result.domain_status or "",
        "domain_available": (
            ""
            if result.domain_available is None
            else result.domain_available
        ),
        "target_positioning": result.target_positioning,
        "pronunciation": result.pronunciation,
        "meaning": result.meaning,
        "brand_story": result.brand_story,
        "tagline": result.tagline,
        "logo_idea": result.logo_idea,
        "vc_score": result.vc_score,
        "vc_reasoning": result.vc_reasoning,
        "vc_main_risk": result.vc_main_risk,
        "memorability_score": result.memorability_score,
        "enterprise_score": result.enterprise_score,
        "international_score": (
            result.international_score
        ),
        "differentiation_score": (
            result.differentiation_score
        ),
    }


def export_results(
    results: list[FinalBrandResult],
    output_file: Path,
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
                result_to_row(
                    result=result,
                    rank=rank,
                )
            )


def run_generation_round(
    service: BrandFinderAIService,
    domain_checker: DomainChecker,
    round_number: int,
) -> list[FinalBrandResult]:
    print("\n")
    print("=" * 68)
    print(
        f"GENERÁLÁSI KÖR "
        f"{round_number}/{MAX_GENERATION_ROUNDS}"
    )
    print("=" * 68)

    (
        generation_result,
        _vc_result,
        _marketing_result,
        final_results,
    ) = service.run_ai_workflow()

    print("\nNaming strategy")
    print("-" * 68)
    print(generation_result.naming_strategy.strip())

    if not final_results:
        print(
            "\nEbben a körben egyetlen név sem ment át "
            "mindkét AI-értékelésen."
        )
        return []

    print(
        "\n[4/4] Domain Checker: "
        ".ai domainek ellenőrzése...",
        flush=True,
    )

    return domain_checker.check_results(final_results)


def main() -> int:
    print_header()

    all_checked_results: list[FinalBrandResult] = []

    try:
        service = BrandFinderAIService()

        with DomainChecker() as domain_checker:
            for round_number in range(
                1,
                MAX_GENERATION_ROUNDS + 1,
            ):
                round_results = run_generation_round(
                    service=service,
                    domain_checker=domain_checker,
                    round_number=round_number,
                )

                all_checked_results.extend(round_results)

                all_checked_results = unique_results(
                    all_checked_results
                )

                print_round_summary(
                    round_number=round_number,
                    round_results=round_results,
                    all_results=all_checked_results,
                )

                available = available_results(
                    all_checked_results
                )

                if (
                    len(available)
                    >= MIN_AVAILABLE_DOMAINS
                ):
                    print(
                        "\nA cél teljesült: "
                        f"{len(available)} szabadnak "
                        "tűnő .ai domaint találtunk."
                    )
                    break

                if (
                    round_number
                    < MAX_GENERATION_ROUNDS
                ):
                    missing = (
                        MIN_AVAILABLE_DOMAINS
                        - len(available)
                    )

                    print(
                        "\nMég "
                        f"{missing} szabadnak tűnő "
                        "domain szükséges."
                    )
                    print(
                        "Automatikusan indul "
                        "a következő generálási kör..."
                    )

        all_checked_results.sort(
            key=lambda result: (
                result.domain_available is True,
                result.final_score,
            ),
            reverse=True,
        )

        final_available_results = available_results(
            all_checked_results
        )

        print_results(final_available_results)

        export_results(
            results=final_available_results,
            output_file=OUTPUT_FILE,
        )

        export_results(
            results=all_checked_results,
            output_file=ALL_RESULTS_FILE,
        )

        print("=" * 68)
        print(f"Szabad domainek CSV: {OUTPUT_FILE}")
        print(f"Összes eredmény CSV: {ALL_RESULTS_FILE}")
        print("=" * 68)

        if (
            len(final_available_results)
            < MIN_AVAILABLE_DOMAINS
        ):
            print(
                "\nFigyelem: a maximális számú kör után "
                f"csak {len(final_available_results)} "
                "szabadnak tűnő domaint találtunk."
            )

        print(
            "\nMegjegyzés: a 'possibly_available' státusz "
            "nem garantálja a domain regisztrálhatóságát. "
            "A kiválasztott neveket mindig ellenőrizd "
            "domainregisztrátornál és védjegyadatbázisban is."
        )

        return 0

    except KeyboardInterrupt:
        print("\nA futtatást megszakítottad.")
        return 130

    except Exception as exc:
        print("\nHIBA")
        print("-" * 68)
        print(
            f"{type(exc).__name__}: {exc}"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())