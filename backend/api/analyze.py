from fastapi import APIRouter, HTTPException

from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import AnalyzeResponse
from tools.brand_intelligence.pipeline import (
    BrandIntelligencePipeline,
)
from tools.brand_intelligence.report_generator import (
    HtmlReportGenerator,
)

router = APIRouter(
    prefix="/analyze",
    tags=["Analysis"],
)

pipeline = BrandIntelligencePipeline()
report_generator = HtmlReportGenerator()


@router.post(
    "",
    response_model=AnalyzeResponse,
)
async def analyze(
    request: AnalyzeRequest,
):
    try:
        candidate = pipeline.analyze_name(
            name=request.name,
            product_description=request.product,
            target_market=request.market,
        )

        report_path = report_generator.save(
            candidate,
            f"tools/brand_intelligence/reports/{candidate.name.lower()}_report.html",
        )

        return AnalyzeResponse(
            success=True,
            report_path=str(report_path),
            overall_score=candidate.final_score,
            rejected=candidate.rejected,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )