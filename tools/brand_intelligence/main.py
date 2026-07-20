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

    return parser.parse_args()


def create_report_filename(name: str) -> str:
    normalized_name = (
        name.strip()
        .lower()
        .replace(" ", "-")
    )

    return f"{normalized_name}_report.json"


def main() -> None:
    args = parse_arguments()

    pipeline = BrandIntelligencePipeline()

    candidate = pipeline.analyze_name(
        name=args.name,
        product_description=args.product,
        target_market=args.market,
    )

    report = {
        "generated_at": pipeline.generated_at(),
        "candidate": candidate.model_dump(mode="json"),
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
    print(f"Domain score: {candidate.domain_score}/10")
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
        print("Nem találtunk hiteles cégnévütközést.")
    else:
        for match in candidate.company_matches:
            print(
                f"{match.name:<30} "
                f"{match.similarity_score:>5.1f}/100 "
                f"[{match.conflict_risk.value}]"
            )

            if match.website:
                print(f"  Web: {match.website}")

            if match.details:
                print(f"  Indoklás: {match.details}")

    print()

    if candidate.rejected:
        print("EREDMÉNY: ELUTASÍTANDÓ")

        for reason in candidate.rejection_reasons:
            print(f"- {reason}")
    else:
        print("EREDMÉNY: TOVÁBBI VIZSGÁLATRA ALKALMAS")

    print()
    print(f"Riport elmentve: {report_path}")


if __name__ == "__main__":
    main()