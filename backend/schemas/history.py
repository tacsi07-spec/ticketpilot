from datetime import datetime

from pydantic import BaseModel, ConfigDict


class HistoryItemResponse(BaseModel):
    id: int
    name: str
    product_description: str
    target_market: str
    overall_score: float
    rejected: bool
    report_path: str
    status: str
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )