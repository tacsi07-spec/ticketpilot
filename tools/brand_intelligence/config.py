from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BrandIntelligenceConfig:
    domain_extensions: tuple[str, ...] = (
        "com",
        "ai",
        "io",
        "de",
        "app",
        "dev",
        "co",
    )

    domain_timeout_seconds: float = 10.0
    domain_request_delay_seconds: float = 0.4

    available_domain_score: float = 10.0
    registered_domain_score: float = 0.0
    unknown_domain_score: float = 3.0

    important_extensions: tuple[str, ...] = (
        "com",
        "ai",
        "de",
    )

    user_agent: str = (
        "BrandIntelligence/0.1 "
        "(domain availability research)"
    )


DEFAULT_CONFIG = BrandIntelligenceConfig()