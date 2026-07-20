from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from tools.brand_intelligence.models import CompanyMatch


class CompanySearchCache:
    CACHE_VERSION = 1

    def __init__(
        self,
        cache_directory: str | Path | None = None,
        ttl_days: int = 7,
    ) -> None:
        if ttl_days < 1:
            raise ValueError(
                "A cache élettartamának legalább 1 napnak kell lennie."
            )

        self.cache_directory = Path(
            cache_directory
            or Path("tools")
            / "brand_intelligence"
            / "cache"
            / "company_search"
        )

        self.ttl = timedelta(days=ttl_days)

        self.cache_directory.mkdir(
            parents=True,
            exist_ok=True,
        )

    @staticmethod
    def _normalize_value(value: str) -> str:
        return re.sub(
            r"\s+",
            " ",
            value.strip().lower(),
        )

    def _build_key(
        self,
        brand_name: str,
        product_description: str,
        market: str,
    ) -> str:
        payload = {
            "cache_version": self.CACHE_VERSION,
            "brand_name": self._normalize_value(
                brand_name
            ),
            "product_description": self._normalize_value(
                product_description
            ),
            "market": self._normalize_value(
                market
            ),
        }

        serialized = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )

        return hashlib.sha256(
            serialized.encode("utf-8")
        ).hexdigest()

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(
            r"[^a-z0-9]+",
            "-",
            value.strip().lower(),
        ).strip("-")

        return slug or "brand"

    def _get_cache_path(
        self,
        brand_name: str,
        product_description: str,
        market: str,
    ) -> Path:
        cache_key = self._build_key(
            brand_name=brand_name,
            product_description=product_description,
            market=market,
        )

        slug = self._slugify(brand_name)

        return self.cache_directory / (
            f"{slug}_{cache_key[:16]}.json"
        )

    def load(
        self,
        brand_name: str,
        product_description: str,
        market: str,
    ) -> list[CompanyMatch] | None:
        cache_path = self._get_cache_path(
            brand_name=brand_name,
            product_description=product_description,
            market=market,
        )

        if not cache_path.exists():
            return None

        try:
            raw_data = json.loads(
                cache_path.read_text(
                    encoding="utf-8"
                )
            )
        except (
            OSError,
            json.JSONDecodeError,
        ):
            return None

        if (
            raw_data.get("cache_version")
            != self.CACHE_VERSION
        ):
            return None

        expires_at_raw = raw_data.get("expires_at")

        if not isinstance(expires_at_raw, str):
            return None

        try:
            expires_at = datetime.fromisoformat(
                expires_at_raw
            )
        except ValueError:
            return None

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if datetime.now(timezone.utc) >= expires_at:
            return None

        matches_data = raw_data.get("matches")

        if not isinstance(matches_data, list):
            return None

        try:
            return [
                CompanyMatch.model_validate(item)
                for item in matches_data
            ]
        except Exception:
            return None

    def save(
        self,
        brand_name: str,
        product_description: str,
        market: str,
        matches: list[CompanyMatch],
    ) -> Path:
        cache_path = self._get_cache_path(
            brand_name=brand_name,
            product_description=product_description,
            market=market,
        )

        created_at = datetime.now(timezone.utc)
        expires_at = created_at + self.ttl

        payload: dict[str, Any] = {
            "cache_version": self.CACHE_VERSION,
            "created_at": created_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "query": {
                "brand_name": brand_name,
                "product_description": (
                    product_description
                ),
                "market": market,
            },
            "matches": [
                match.model_dump(
                    mode="json"
                )
                for match in matches
            ],
        }

        temporary_path = cache_path.with_suffix(
            ".tmp"
        )

        temporary_path.write_text(
            json.dumps(
                payload,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        temporary_path.replace(cache_path)

        return cache_path

    def delete(
        self,
        brand_name: str,
        product_description: str,
        market: str,
    ) -> bool:
        cache_path = self._get_cache_path(
            brand_name=brand_name,
            product_description=product_description,
            market=market,
        )

        if not cache_path.exists():
            return False

        cache_path.unlink()
        return True