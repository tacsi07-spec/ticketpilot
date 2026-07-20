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

    company_search_model: str = "gpt-5.6"

    company_search_context_size: str = "low"

    company_search_max_results: int = 8

    company_conflict_threshold: float = 75.0
    company_warning_threshold: float = 45.0


DEFAULT_CONFIG = BrandIntelligenceConfig()