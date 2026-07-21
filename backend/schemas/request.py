from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


DEFAULT_MARKET = (
    "Germany, European Union and "
    "international B2B market"
)


class AnalyzeRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=80,
        description="The proposed brand name.",
        examples=["Cendora"],
    )

    product: str = Field(
        min_length=10,
        max_length=500,
        description=(
            "A short description of the product, "
            "service or company."
        ),
        examples=[
            "AI-powered IT support assistant"
        ],
    )

    market: str = Field(
        default=DEFAULT_MARKET,
        min_length=2,
        max_length=200,
        description="The target market.",
        examples=[
            "Germany and European Union"
        ],
    )

    @field_validator(
        "name",
        "product",
        "market",
        mode="before",
    )
    @classmethod
    def strip_whitespace(
        cls,
        value: object,
    ) -> object:
        if isinstance(value, str):
            return value.strip()

        return value

    @field_validator("name")
    @classmethod
    def validate_name(
        cls,
        value: str,
    ) -> str:
        if not any(
            character.isalnum()
            for character in value
        ):
            raise ValueError(
                "Brand name must contain at least "
                "one letter or number."
            )

        return value