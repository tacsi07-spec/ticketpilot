from __future__ import annotations

import csv
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests


# -------------------------------------------------------------------
# Beállítások
# -------------------------------------------------------------------

GENERATE_COUNT = 10_000
MAX_DOMAIN_CHECKS = 300
REQUEST_DELAY_SECONDS = 1.0

OUTPUT_FILE = Path("available_ai_domains.csv")

RDAP_BASE_URL = (
    "https://rdap.identitydigital.services/rdap/domain/"
)


# -------------------------------------------------------------------
# Névépítő elemek
# -------------------------------------------------------------------

STARTS = [
    "av",
    "br",
    "cal",
    "cor",
    "del",
    "el",
    "ev",
    "fal",
    "hel",
    "kal",
    "kor",
    "lum",
    "mel",
    "nav",
    "nel",
    "nor",
    "or",
    "rav",
    "rel",
    "sen",
    "sol",
    "tal",
    "tel",
    "val",
    "vel",
    "ver",
    "zor",
]

MIDDLES = [
    "a",
    "e",
    "i",
    "o",
    "ai",
    "en",
    "er",
    "ev",
    "in",
    "ir",
    "iv",
    "on",
    "or",
    "ov",
    "ul",
]

ENDS = [
    "ra",
    "ria",
    "rio",
    "rix",
    "ron",
    "va",
    "via",
    "vio",
    "vora",
    "vra",
    "xa",
    "xia",
    "xo",
    "ya",
    "yon",
    "zen",
]

FORBIDDEN_PARTS = [
    "sex",
    "xxx",
    "fuck",
    "shit",
    "nazi",
    "kill",
    "drug",
    "porn",
]

AWKWARD_PATTERNS = [
    r"[aeiou]{3,}",
    r"[^aeiou]{5,}",
    r"(.)\1\1",
]


# -------------------------------------------------------------------
# Eredménytípus
# -------------------------------------------------------------------

@dataclass
class DomainResult:
    name: str
    domain: str
    status: str


# -------------------------------------------------------------------
# Név generálása
# -------------------------------------------------------------------

def generate_name() -> str:
    start = random.choice(STARTS)
    middle = random.choice(MIDDLES)
    end = random.choice(ENDS)

    return f"{start}{middle}{end}".lower()


def is_valid_name(name: str) -> bool:
    if not 6 <= len(name) <= 10:
        return False

    if not name.isalpha():
        return False

    if any(part in name for part in FORBIDDEN_PARTS):
        return False

    if any(re.search(pattern, name) for pattern in AWKWARD_PATTERNS):
        return False

    # Legyen benne legalább két magánhangzó.
    vowel_count = sum(
        character in "aeiouy"
        for character in name
    )

    if vowel_count < 2:
        return False

    return True


def score_name(name: str) -> int:
    score = 100

    # A rövidebb nevek általában könnyebben megjegyezhetők.
    score -= abs(len(name) - 7) * 4

    # Kerüljük a túl sok ritka betűt.
    score -= name.count("x") * 3
    score -= name.count("z") * 2

    # Enyhe előny a kellemesebb végződéseknek.
    preferred_endings = (
        "ra",
        "ria",
        "rio",
        "via",
        "vio",
        "va",
    )

    if name.endswith(preferred_endings):
        score += 5

    return score


def generate_names(count: int) -> list[str]:
    generated: set[str] = set()

    attempts = 0
    maximum_attempts = count * 30

    while (
        len(generated) < count
        and attempts < maximum_attempts
    ):
        attempts += 1
        name = generate_name()

        if is_valid_name(name):
            generated.add(name)

    return sorted(
        generated,
        key=score_name,
        reverse=True,
    )


# -------------------------------------------------------------------
# Domain ellenőrzése RDAP segítségével
# -------------------------------------------------------------------

def check_ai_domain(
    session: requests.Session,
    name: str,
) -> DomainResult:
    domain = f"{name}.ai"
    url = f"{RDAP_BASE_URL}{domain}"

    try:
        response = session.get(
            url,
            timeout=15,
            headers={
                "Accept": "application/rdap+json",
                "User-Agent": (
                    "DomainNameFinder/1.0 "
                    "(personal availability research)"
                ),
            },
        )

        if response.status_code == 404:
            return DomainResult(
                name=name,
                domain=domain,
                status="possibly_available",
            )

        if response.status_code == 200:
            return DomainResult(
                name=name,
                domain=domain,
                status="registered",
            )

        if response.status_code == 429:
            return DomainResult(
                name=name,
                domain=domain,
                status="rate_limited",
            )

        return DomainResult(
            name=name,
            domain=domain,
            status=f"unknown_{response.status_code}",
        )

    except requests.RequestException:
        return DomainResult(
            name=name,
            domain=domain,
            status="request_error",
        )


# -------------------------------------------------------------------
# CSV mentése
# -------------------------------------------------------------------

def save_results(results: list[DomainResult]) -> None:
    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "name",
                "domain",
                "status",
                "brand_score",
            ]
        )

        for result in results:
            writer.writerow(
                [
                    result.name,
                    result.domain,
                    result.status,
                    score_name(result.name),
                ]
            )


# -------------------------------------------------------------------
# Program indítása
# -------------------------------------------------------------------

def main() -> None:
    print("Márkanevek generálása...")

    names = generate_names(GENERATE_COUNT)

    if not names:
        print("Nem sikerült neveket generálni.")
        return

    names_to_check = names[:MAX_DOMAIN_CHECKS]

    print(f"{len(names)} egyedi név generálva.")
    print(
        f"Az első {len(names_to_check)} "
        ".ai domain ellenőrzése indul."
    )
    print()

    results: list[DomainResult] = []

    with requests.Session() as session:
        for index, name in enumerate(
            names_to_check,
            start=1,
        ):
            result = check_ai_domain(
                session=session,
                name=name,
            )

            results.append(result)

            print(
                f"[{index}/{len(names_to_check)}] "
                f"{result.domain}: {result.status}"
            )

            if result.status == "rate_limited":
                print(
                    "A szerver korlátozta a lekérdezéseket. "
                    "60 másodperc várakozás..."
                )
                time.sleep(60)
            else:
                time.sleep(REQUEST_DELAY_SECONDS)

    results.sort(
        key=lambda item: (
            item.status != "possibly_available",
            -score_name(item.name),
        )
    )

    save_results(results)

    available = [
        result
        for result in results
        if result.status == "possibly_available"
    ]

    print()
    print("----------------------------------------")
    print(
        f"Szabadnak tűnő domainek: {len(available)}"
    )
    print("----------------------------------------")

    for result in available[:30]:
        print(
            f"{result.domain:<24} "
            f"pontszám: {score_name(result.name)}"
        )

    print()
    print(f"Eredményfájl: {OUTPUT_FILE.resolve()}")
    print()
    print(
        "Fontos: a 'possibly_available' nem garantálja, "
        "hogy a domain ténylegesen megvásárolható. "
        "A végső ellenőrzést mindig egy regisztrátornál végezd el."
    )


if __name__ == "__main__":
    main()