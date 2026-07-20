from __future__ import annotations

import argparse
import json
from pathlib import Path

from tools.brand_intelligence.pipeline import (
    BrandIntelligencePipeline,
)


REPORTS_DIRECTORY = Path(
    "tools/brand_intelligence/reports"
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Startup- és SaaS-márkanevek "
            "brand intelligence elemzése."
        )
    )

    parser.add_argument(
        "name",
        help="Az ellenőrizendő márkanév.",
    )

    parser.add_argument(
        "--product",
        required=True,
        help="A tervezett termék rövid leírása.",
    )

    parser.add_argument(
        "--market",
        default=(
            "Germany, European Union "
            "and international B2B market"
        ),
        help="A célpiac leírása.",
    )

    cache_group = parser.add_mutually_exclusive_group()

    cache_group.add_argument(
        "--refresh-company-cache",
        action="store_true",
        help=(
            "Új OpenAI webes cégnévkeresést indít, "
            "majd felülírja a meglévő cache-t."
        ),
    )

    cache_group.add_argument(
        "--no-company-cache",
        action="store_true",
        help=(
            "Kikapcsolja a company cache használatát. "
            "Minden futás új OpenAI API-hívást indít."
        ),
    )

    return parser.parse_args()


def create_report_filename(name: str) -> str:
    normalized_name = (
        name.strip()
        .lower()
        .replace(" ", "-")
    )

    return f"{normalized_name}_report.json"


def describe_cache_status(status: str) -> str:
    descriptions = {
        "hit": (
            "HIT – meglévő eredmény betöltve, "
            "nem történt OpenAI API-hívás"
        ),
        "miss": (
            "MISS – nem volt érvényes cache, "
            "OpenAI keresés történt és az eredmény elmentve"
        ),
        "refreshed": (
            "REFRESHED – új OpenAI keresés történt, "
            "a cache frissítve lett"
        ),
        "disabled": (
            "DISABLED – a cache ki volt kapcsolva, "
            "OpenAI keresés történt"
        ),
    }

    return descriptions.get(
        status,
        status.upper(),
    )


def main() -> None:
    args = parse_arguments()

    pipeline = BrandIntelligencePipeline()

    use_company_cache = not args.no_company_cache

    candidate = pipeline.analyze_name(
        name=args.name,
        product_description=args.product,
        target_market=args.market,
        use_company_cache=use_company_cache,
        refresh_company_cache=(
            args.refresh_company_cache
        ),
    )

    cache_status = pipeline.last_company_cache_status

    report = {
        "generated_at": pipeline.generated_at(),
        "company_cache": {
            "status": cache_status,
            "enabled": use_company_cache,
            "refresh_requested": (
                args.refresh_company_cache
            ),
        },
        "candidate": candidate.model_dump(
            mode="json"
        ),
    }

    REPORTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    report_path = (
        REPORTS_DIRECTORY
        / create_report_filename(args.name)
    )

    report_path.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print()
    print(f"Brand: {candidate.name}")
    print(
        "Company cache: "
        f"{describe_cache_status(cache_status)}"
    )
    print()
    print(
        f"Domain score: "
        f"{candidate.domain_score}/10"
    )
    print()

    for domain in candidate.domains:
        availability = (
            "VALÓSZÍNŰLEG SZABAD"
            if domain.possibly_available is True
            else "FOGLALT"
            if domain.possibly_available is False
            else "ISMERETLEN"
        )

        print(
            f"{domain.domain:<20} "
            f"{availability:<22} "
            f"[{domain.status.value}]"
        )

    print()
    print(
        "Company conflict score: "
        f"{candidate.company_conflict_score}/10"
    )
    print()

    if not candidate.company_matches:
        print(
            "Nem találtunk hiteles "
            "cégnévütközést."
        )
    else:
        for match in candidate.company_matches:
            print(
                f"{match.name:<30} "
                f"{match.similarity_score:>5.1f}/100 "
                f"[{match.conflict_risk.value}]"
            )

            if match.website:
                print(
                    f"  Web: {match.website}"
                )

            if match.details:
                print(
                    f"  Indoklás: {match.details}"
                )

    print()
    print(
        "Similarity score: "
        f"{candidate.similarity_score}/10"
    )
    print()

    if not candidate.similarity_results:
        print(
            "Nincs összehasonlítható cégnév."
        )
    else:
        for result in candidate.similarity_results:
            print(
                f"{result.compared_name:<30} "
                f"{result.final_score:>5.1f}/100 "
                f"[{result.status.value}]"
            )

            if (
                result.canonical_compared.lower()
                != result.compared_name.lower()
            ):
                print(
                    "  Canonical név: "
                    f"{result.canonical_compared}"
                )

    print()

    if candidate.rejected:
        print("EREDMÉNY: ELUTASÍTANDÓ")

        for reason in candidate.rejection_reasons:
            print(f"- {reason}")
    else:
        print(
            "EREDMÉNY: "
            "TOVÁBBI VIZSGÁLATRA ALKALMAS"
        )

    print()
    print(
        f"Riport elmentve: {report_path}"
    )


if __name__ == "__main__":
    main()