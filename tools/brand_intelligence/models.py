from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CheckStatus(str, Enum):
    CLEAR = "clear"
    WARNING = "warning"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"
    MANUAL_REVIEW = "manual_review"


class DomainCheckResult(BaseModel):
    extension: str
    domain: str
    status: CheckStatus
    possibly_available: bool | None = None
    details: str = ""


class CompanyMatch(BaseModel):
    name: str
    website: str | None = None
    industry: str | None = None
    country: str | None = None
    similarity_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )
    conflict_risk: CheckStatus = CheckStatus.UNKNOWN
    details: str = ""


class SocialCheckResult(BaseModel):
    platform: str
    username: str
    status: CheckStatus
    profile_url: str | None = None
    details: str = ""


class TrademarkCheckResult(BaseModel):
    database: str
    query: str
    status: CheckStatus
    matching_marks: list[str] = Field(default_factory=list)
    details: str = ""
    manual_review_required: bool = True


class BrandCandidate(BaseModel):
    name: str
    pronunciation: str = ""
    meaning: str = ""
    tagline: str = ""

    domains: list[DomainCheckResult] = Field(
        default_factory=list
    )
    company_matches: list[CompanyMatch] = Field(
        default_factory=list
    )
    social_results: list[SocialCheckResult] = Field(
        default_factory=list
    )
    trademark_results: list[TrademarkCheckResult] = Field(
        default_factory=list
    )

    linguistic_score: float = 0.0
    originality_score: float = 0.0
    domain_score: float = 0.0
    company_conflict_score: float = 0.0
    social_score: float = 0.0
    trademark_score: float = 0.0
    final_score: float = 0.0

    rejected: bool = False
    rejection_reasons: list[str] = Field(
        default_factory=list
    )


class BrandIntelligenceReport(BaseModel):
    product_description: str
    target_market: str
    candidates: list[BrandCandidate]
    recommended_names: list[str] = Field(
        default_factory=list
    )
    generated_at: str