from pydantic import BaseModel


class AnalyzeResponse(BaseModel):
    success: bool
    report_path: str
    overall_score: float
    rejected: bool