from pydantic import BaseModel, Field


class BrandCandidate(BaseModel):
    name: str = Field(
        description="The proposed brand name without a domain extension."
    )
    pronunciation: str = Field(
        description="A simple English pronunciation guide."
    )
    meaning: str = Field(
        description="The conceptual meaning or inspiration behind the name."
    )
    brand_story: str = Field(
        description="A short brand story explaining why the name fits the product."
    )
    tagline: str = Field(
        description="A short and memorable English tagline."
    )
    logo_idea: str = Field(
        description="A concise visual direction for the logo."
    )
    target_positioning: str = Field(
        description="The market positioning, such as premium, enterprise, modern, or technical."
    )


class BrandGenerationResult(BaseModel):
    naming_strategy: str = Field(
        description="The naming philosophy derived from the reference names."
    )
    candidates: list[BrandCandidate]


class VCReview(BaseModel):
    name: str
    approved: bool
    score: int = Field(ge=0, le=100)
    reasoning: str
    main_risk: str


class VCReviewResult(BaseModel):
    reviews: list[VCReview]


class MarketingReview(BaseModel):
    name: str
    approved: bool
    memorability_score: int = Field(ge=0, le=100)
    enterprise_score: int = Field(ge=0, le=100)
    international_score: int = Field(ge=0, le=100)
    differentiation_score: int = Field(ge=0, le=100)
    reasoning: str


class MarketingReviewResult(BaseModel):
    reviews: list[MarketingReview]


class FinalBrandResult(BaseModel):
    name: str
    pronunciation: str
    meaning: str
    brand_story: str
    tagline: str
    logo_idea: str
    target_positioning: str

    vc_score: int
    vc_reasoning: str
    vc_main_risk: str

    memorability_score: int
    enterprise_score: int
    international_score: int
    differentiation_score: int

    final_score: float
    domain: str | None = None
    domain_status: str | None = None
    domain_available: bool | None = None
    domain_bonus: float = 0.0
