from __future__ import annotations

import argparse
import json
import logging
import os
import re
import sys
import webbrowser
from pathlib import Path
from typing import Any

from tools.brand_intelligence.models import BrandCandidate
from tools.brand_intelligence.pipeline import (
    BrandIntelligencePipeline,
)
from tools.brand_intelligence.report_generator import (
    HtmlReportGenerator,
)


DEFAULT_MARKET = (
    "Germany, European Union and "
    "international B2B market"
)

DEFAULT_REPORT_DIRECTORY = Path(
    "tools/brand_intelligence/reports"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="brandintel",
        description=(
            "Analyze a proposed brand name and generate "
            "a Brand Intelligence report."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--name",
        required=True,
        help="The proposed brand name.",
    )

    parser.add_argument(
        "--product",
        required=True,
        help=(
            "Short description of the product, service "
            "or company."
        ),
    )

    parser.add_argument(
        "--market",
        default=DEFAULT_MARKET,
        help="Target market for company and legal research.",
    )

    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Custom output path for the HTML report. "
            "When omitted, a filename is generated automatically."
        ),
    )

    parser.add_argument(
        "--no-report",
        action="store_true",
        help="Do not generate an HTML report.",
    )

    parser.add_argument(
        "--json",
        action="store_true",
        dest="print_json",
        help="Print the complete analysis result as JSON.",
    )

    parser.add_argument(
        "--json-output",
        type=Path,
        help="Save the complete analysis result to a JSON file.",
    )

    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable the company-search cache.",
    )

    parser.add_argument(
        "--refresh-cache",
        action="store_true",
        help=(
            "Ignore an existing company-search cache entry "
            "and replace it with fresh results."
        ),
    )

    parser.add_argument(
        "--open",
        action="store_true",
        dest="open_report",
        help="Open the generated HTML report in the browser.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable detailed logging.",
    )

    return parser


def configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.INFO if verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )


def slugify(value: str) -> str:
    normalized = value.strip().lower()

    normalized = re.sub(
        r"[^a-z0-9]+",
        "-",
        normalized,
    )

    normalized = normalized.strip("-")

    return normalized or "brand"


def default_report_path(
    brand_name: str,
) -> Path:
    filename = f"{slugify(brand_name)}_report.html"

    return DEFAULT_REPORT_DIRECTORY / filename


def candidate_to_dict(
    candidate: BrandCandidate,
) -> dict[str, Any]:
    """
    Convert a Pydantic model to a JSON-compatible dictionary.

    Supports both Pydantic v2 and v1.
    """

    if hasattr(candidate, "model_dump"):
        return candidate.model_dump(
            mode="json",
        )

    if hasattr(candidate, "dict"):
        return candidate.dict()

    raise TypeError(
        "BrandCandidate cannot be serialized."
    )


def candidate_to_json(
    candidate: BrandCandidate,
) -> str:
    return json.dumps(
        candidate_to_dict(candidate),
        indent=2,
        ensure_ascii=False,
    )


def save_json_result(
    candidate: BrandCandidate,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        candidate_to_json(candidate),
        encoding="utf-8",
    )

    return output_path.resolve()


def format_score(score: float | None) -> str:
    if score is None:
        return "N/A"

    return f"{score:.2f} / 10"


def print_header(
    name: str,
    product: str,
    market: str,
) -> None:
    print()
    print("=" * 64)
    print("BRAND INTELLIGENCE")
    print("=" * 64)
    print(f"Brand:   {name}")
    print(f"Product: {product}")
    print(f"Market:  {market}")
    print("-" * 64)


def print_summary(
    candidate: BrandCandidate,
    cache_status: str,
) -> None:
    recommendation = (
        "REJECTED / MANUAL REVIEW REQUIRED"
        if candidate.rejected
        else "RECOMMENDED FOR CONTINUED EVALUATION"
    )

    print()
    print("Analysis completed.")
    print()
    print(f"Overall score:    {format_score(candidate.final_score)}")
    print(f"Domain score:     {format_score(candidate.domain_score)}")
    print(
        "Company score:    "
        f"{format_score(candidate.company_conflict_score)}"
    )
    print(
        "Similarity score: "
        f"{format_score(candidate.similarity_score)}"
    )
    print(
        "Legal score:      "
        f"{format_score(candidate.trademark_score)}"
    )
    print(f"Company cache:    {cache_status}")
    print()
    print(f"Recommendation:   {recommendation}")

    if candidate.rejection_reasons:
        print()
        print("Risk findings:")

        for reason in candidate.rejection_reasons:
            print(f"  - {reason}")

    print()


def validate_arguments(
    args: argparse.Namespace,
    parser: argparse.ArgumentParser,
) -> None:
    if args.no_cache and args.refresh_cache:
        parser.error(
            "--no-cache and --refresh-cache "
            "cannot be used together."
        )

    if args.no_report and args.open_report:
        parser.error(
            "--open requires HTML report generation. "
            "Remove --no-report."
        )

    if args.output and args.no_report:
        parser.error(
            "--output cannot be used together with --no-report."
        )

    if not args.name.strip():
        parser.error("--name cannot be empty.")

    if not args.product.strip():
        parser.error("--product cannot be empty.")

    if not args.market.strip():
        parser.error("--market cannot be empty.")


def open_html_report(
    report_path: Path,
) -> bool:
    try:
        report_uri = report_path.resolve().as_uri()
        return webbrowser.open(report_uri)
    except (OSError, ValueError):
        return False


def run_analysis(
    args: argparse.Namespace,
) -> int:
    pipeline = BrandIntelligencePipeline()

    print_header(
        name=args.name,
        product=args.product,
        market=args.market,
    )

    print("Running domain, company, similarity and legal checks...")
    print("This may take a few moments.")

    candidate = pipeline.analyze_name(
        name=args.name.strip(),
        product_description=args.product.strip(),
        target_market=args.market.strip(),
        use_company_cache=not args.no_cache,
        refresh_company_cache=args.refresh_cache,
    )

    print_summary(
        candidate=candidate,
        cache_status=pipeline.last_company_cache_status,
    )

    report_path: Path | None = None

    if not args.no_report:
        report_path = (
            args.output
            if args.output is not None
            else default_report_path(candidate.name)
        )

        report_path = HtmlReportGenerator().save(
            candidate=candidate,
            output_path=report_path,
        )

        print(f"HTML report: {report_path}")

    if args.json_output is not None:
        json_path = save_json_result(
            candidate=candidate,
            output_path=args.json_output,
        )

        print(f"JSON result: {json_path}")

    if args.print_json:
        print()
        print(candidate_to_json(candidate))

    if args.open_report and report_path is not None:
        opened = open_html_report(report_path)

        if not opened:
            print(
                "Warning: the report could not be opened "
                "automatically.",
                file=sys.stderr,
            )

    return 0


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    validate_arguments(
        args=args,
        parser=parser,
    )

    configure_logging(args.verbose)

    try:
        return run_analysis(args)

    except KeyboardInterrupt:
        print(
            "\nAnalysis cancelled by user.",
            file=sys.stderr,
        )
        return 130

    except ValueError as exc:
        print(
            f"Input error: {exc}",
            file=sys.stderr,
        )
        return 2

    except Exception as exc:
        logging.exception(
            "Brand Intelligence analysis failed."
        )

        print(
            f"Analysis failed: {exc}",
            file=sys.stderr,
        )

        print(
            "Run the command again with --verbose "
            "for more information.",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())