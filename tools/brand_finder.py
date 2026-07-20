from __future__ import annotations

import csv
import os
import re
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


# ---------------------------------------------------------
# Beállítások
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ENV_FILE = PROJECT_ROOT / "backend" / ".env"
OUTPUT_FILE = PROJECT_ROOT / "brand_finder_results.csv"

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

BATCH_COUNT = 3
NAMES_PER_BATCH = 40

MAX_DOMAIN_CHECKS = 100
REQUEST_DELAY_SECONDS = 1.0

RDAP_BASE_URL = "https://rdap.identitydigital.services/rdap/domain/"


# ---------------------------------------------------------
# Strukturált AI-válasz
# ---------------------------------------------------------

class BrandCandidate(BaseModel):
    name: str = Field(
        description="An original invented brand name."
    )
    reason: str = Field(
        description="A short explanation of why the name works."
    )
    style: str = Field(
        description="The perceived brand style."
    )
    ai_score: int = Field(
        ge=0,
        le=100,
        description="Brand quality score from 0 to 100."
    )


class BrandBatch(BaseModel):
    candidates: list[BrandCandidate]


# ---------------------------------------------------------
# Környezeti változók
# ---------------------------------------------------------

def load_environment() -> None:
    if BACKEND_ENV_FILE.exists():
        load_dotenv(BACKEND_ENV_FILE)
    else:
        load_dotenv()

    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "Nem található az OPENAI_API_KEY.\n"
            f"Ellenőrizd ezt a fájlt: {BACKEND_ENV_FILE}"
        )


# ---------------------------------------------------------
# Névellenőrzés
# ---------------------------------------------------------

FORBIDDEN_WORDS = {
    "ai",
    "gpt",
    "ticket",
    "desk",
    "help",
    "support",
    "pilot",
    "copilot",
    "openai",
    "microsoft",
    "google",
    "amazon",
    "apple",
    "meta",
}

FORBIDDEN_NAMES = {
    "notion",
    "linear",
    "cursor",
    "asana",
    "stripe",
    "slack",
    "vercel",
    "figma",
    "miro",
    "zendesk",
    "servicenow",
    "atlassian",
    "jira",
}


def normalize_name(name: str) -> str:
    return re.sub(r"[^a-z]", "", name.lower())


def is_valid_name(name: str) -> bool:
    normalized = normalize_name(name)

    if not 6 <= len(normalized) <= 10:
        return False

    if normalized in FORBIDDEN_NAMES:
        return False

    if any(word in normalized for word in FORBIDDEN_WORDS):
        return False

    if re.search(r"[aeiouy]{4,}", normalized):
        return False

    if re.search(r"[^aeiouy]{5,}", normalized):
        return False

    if re.search(r"(.)\1\1", normalized):
        return False

    vowel_count = sum(
        character in "aeiouy"
        for character in normalized
    )

    return vowel_count >= 2


# ---------------------------------------------------------
# Helyi brandpontszám
# ---------------------------------------------------------

def calculate_local_score(name: str) -> int:
    normalized = normalize_name(name)
    score = 100

    score -= abs(len(normalized) - 8) * 4

    score -= normalized.count("x") * 3
    score -= normalized.count("z") * 2
    score -= normalized.count("q") * 4

    difficult_groups = [
        "rvra",
        "vv",
        "xx",
        "zx",
        "qx",
        "xq",
        "kk",
    ]

    for group in difficult_groups:
        if group in normalized:
            score -= 12

    preferred_endings = (
        "ia",
        "via",
        "ora",
        "era",
        "eva",
        "iva",
        "ara",
        "ria",
        "io",
    )

    if normalized.endswith(preferred_endings):
        score += 5

    return max(0, min(score, 100))


def calculate_final_score(
    candidate: BrandCandidate,
) -> int:
    local_score = calculate_local_score(candidate.name)

    return round(
        candidate.ai_score * 0.65
        + local_score * 0.35
    )


# ---------------------------------------------------------
# AI-generálás
# ---------------------------------------------------------

def generate_brand_batch(
    client: OpenAI,
    batch_number: int,
) -> list[BrandCandidate]:
    prompt = f"""
You are an expert naming strategist for enterprise software companies.

Generate exactly {NAMES_PER_BATCH} original invented brand names for an
AI-powered IT support and IT operations SaaS product.

The product helps internal IT departments:

- analyze support requests,
- diagnose technical problems,
- classify urgency,
- recommend troubleshooting steps,
- generate PowerShell commands,
- prepare replies for users.

Naming requirements:

- invented brand words, not generic product descriptions,
- 6 to 10 letters,
- easy to pronounce in English and German,
- professional and suitable for enterprise customers,
- modern but not childish,
- memorable after hearing it once,
- must not include AI, GPT, ticket, desk, help, support, pilot or copilot,
- must not imitate famous software companies,
- avoid excessive use of X, Z and Q,
- avoid difficult consonant clusters,
- do not generate small spelling variations of the same name,
- names similar in feeling to Lumivia and Senerva are acceptable,
  but do not reproduce those names,
- each name must be substantially different from the others.

This is generation batch number {batch_number}.

For each candidate provide:

- name,
- one-sentence reason,
- style such as enterprise, modern, premium or technical,
- ai_score from 0 to 100.
"""

    response = client.responses.parse(
        model=MODEL,
        input=[
            {
                "role": "system",
                "content": (
                    "Create original, pronounceable and "
                    "professionally brandable company names."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=BrandBatch,
    )

    parsed = response.output_parsed

    if parsed is None:
        raise RuntimeError(
            f"A(z) {batch_number}. AI-generálás nem adott "
            "feldolgozható eredményt."
        )

    return parsed.candidates


def generate_candidates(
    client: OpenAI,
) -> list[BrandCandidate]:
    candidates_by_name: dict[str, BrandCandidate] = {}

    for batch_number in range(1, BATCH_COUNT + 1):
        print(
            f"\nAI-generálás: {batch_number}/{BATCH_COUNT}"
        )

        batch = generate_brand_batch(
            client=client,
            batch_number=batch_number,
        )

        accepted = 0

        for candidate in batch:
            normalized = normalize_name(candidate.name)

            if not is_valid_name(normalized):
                continue

            if normalized in candidates_by_name:
                continue

            candidate.name = normalized.capitalize()
            candidates_by_name[normalized] = candidate
            accepted += 1

        print(
            f"Elfogadott új nevek ebben a körben: {accepted}"
        )

    candidates = list(candidates_by_name.values())

    candidates.sort(
        key=calculate_final_score,
        reverse=True,
    )

    return candidates


# ---------------------------------------------------------
# .ai domain ellenőrzése
# ---------------------------------------------------------

def check_ai_domain(
    session: requests.Session,
    name: str,
) -> str:
    domain = f"{normalize_name(name)}.ai"
    url = f"{RDAP_BASE_URL}{domain}"

    try:
        response = session.get(
            url,
            timeout=20,
            headers={
                "Accept": "application/rdap+json",
                "User-Agent": (
                    "BrandFinder/1.0 "
                    "(personal domain availability research)"
                ),
            },
        )

        if response.status_code == 404:
            return "possibly_available"

        if response.status_code == 200:
            return "registered"

        if response.status_code == 429:
            return "rate_limited"

        return f"unknown_{response.status_code}"

    except requests.RequestException:
        return "request_error"


# ---------------------------------------------------------
# CSV mentése
# ---------------------------------------------------------

def save_results(
    rows: list[dict[str, str | int]],
) -> None:
    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csv_file:
        fieldnames = [
            "name",
            "domain",
            "domain_status",
            "final_score",
            "ai_score",
            "local_score",
            "style",
            "reason",
        ]

        writer = csv.DictWriter(
            csv_file,
            fieldnames=fieldnames,
        )

        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------
# Főprogram
# ---------------------------------------------------------


def main() -> None:
    print("1. main() elindult")

    load_environment()
    print("2. .env betöltve")

    client = OpenAI()
    print("3. OpenAI kliens létrehozva")

    candidates = generate_candidates(client)
    print("4. AI generálás kész")

    if not candidates:
        print("Nem sikerült használható neveket generálni.")
        return

    print(
        f"\nÖsszesen {len(candidates)} egyedi név készült."
    )

    candidates_to_check = candidates[:MAX_DOMAIN_CHECKS]

    print(
        f"A legjobb {len(candidates_to_check)} "
        ".ai domain ellenőrzése következik.\n"
    )

    rows: list[dict[str, str | int]] = []

    with requests.Session() as session:
        for index, candidate in enumerate(
            candidates_to_check,
            start=1,
        ):
            domain = (
                f"{normalize_name(candidate.name)}.ai"
            )

            status = check_ai_domain(
                session=session,
                name=candidate.name,
            )

            final_score = calculate_final_score(candidate)
            local_score = calculate_local_score(
                candidate.name
            )

            print(
                f"[{index}/{len(candidates_to_check)}] "
                f"{domain:<24} "
                f"{status:<20} "
                f"pont: {final_score}"
            )

            rows.append(
                {
                    "name": candidate.name,
                    "domain": domain,
                    "domain_status": status,
                    "final_score": final_score,
                    "ai_score": candidate.ai_score,
                    "local_score": local_score,
                    "style": candidate.style,
                    "reason": candidate.reason,
                }
            )

            if status == "rate_limited":
                print(
                    "Lekérdezési korlátozás. "
                    "60 másodperc várakozás..."
                )
                time.sleep(60)
            else:
                time.sleep(REQUEST_DELAY_SECONDS)

    status_order = {
        "possibly_available": 0,
        "registered": 1,
        "rate_limited": 2,
        "request_error": 3,
    }

    rows.sort(
        key=lambda row: (
            status_order.get(
                str(row["domain_status"]),
                4,
            ),
            -int(row["final_score"]),
        )
    )

    save_results(rows)

    available = [
        row
        for row in rows
        if row["domain_status"]
        == "possibly_available"
    ]

    print("\n" + "=" * 60)
    print(
        f"Szabadnak tűnő domainek: {len(available)}"
    )
    print("=" * 60)

    for row in available[:20]:
        print(
            f"{row['domain']:<24} "
            f"pont: {row['final_score']:<3} "
            f"{row['style']}"
        )

    print(f"\nCSV elkészült:\n{OUTPUT_FILE}")
    print(
        "\nA 'possibly_available' eredményt mindig "
        "ellenőrizd egy domainregisztrátornál is."
    )


if __name__ == "__main__":
    main()