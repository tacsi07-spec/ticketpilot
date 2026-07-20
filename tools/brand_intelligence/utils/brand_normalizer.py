from __future__ import annotations

import re
import unicodedata


class BrandNameNormalizer:
    LEGAL_SUFFIXES: tuple[str, ...] = (
        "ag",
        "bv",
        "corp",
        "corporation",
        "eood",
        "gbr",
        "gmbh",
        "inc",
        "incorporated",
        "kft",
        "kg",
        "llc",
        "llp",
        "ltd",
        "limited",
        "nv",
        "oy",
        "ou",
        "oü",
        "plc",
        "pte",
        "sarl",
        "sas",
        "srl",
        "ug",
    )

    DESCRIPTIVE_SUFFIXES: tuple[str, ...] = (
        "ai",
        "analytics",
        "automation",
        "cloud",
        "consulting",
        "digital",
        "group",
        "labs",
        "platform",
        "software",
        "solutions",
        "systems",
        "technologies",
        "technology",
        "tech",
    )

    @staticmethod
    def _remove_accents(value: str) -> str:
        normalized = unicodedata.normalize(
            "NFKD",
            value,
        )

        return "".join(
            character
            for character in normalized
            if not unicodedata.combining(character)
        )

    @staticmethod
    def _remove_parenthetical_content(value: str) -> str:
        return re.sub(
            r"\([^)]*\)",
            " ",
            value,
        )

    @staticmethod
    def _clean_punctuation(value: str) -> str:
        return re.sub(
            r"[^a-zA-Z0-9\s-]",
            " ",
            value,
        )

    @staticmethod
    def _collapse_whitespace(value: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    def canonicalize(
        self,
        name: str,
    ) -> str:
        if not name or not name.strip():
            raise ValueError(
                "A cégnév nem lehet üres."
            )

        cleaned = self._remove_parenthetical_content(name)
        cleaned = self._remove_accents(cleaned)
        cleaned = self._clean_punctuation(cleaned)
        cleaned = cleaned.replace("-", " ")
        cleaned = self._collapse_whitespace(cleaned)

        words = cleaned.split()

        removable_suffixes = {
            *self.LEGAL_SUFFIXES,
            *self.DESCRIPTIVE_SUFFIXES,
        }

        while len(words) > 1:
            last_word = words[-1].lower().rstrip(".")

            if last_word not in removable_suffixes:
                break

            words.pop()

        canonical_name = " ".join(words).strip()

        if not canonical_name:
            return cleaned

        return canonical_name