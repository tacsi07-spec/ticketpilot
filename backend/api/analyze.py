import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from backend.schemas.error import (
    ErrorDetail,
    ErrorResponse,
)
from backend.schemas.request import AnalyzeRequest
from backend.schemas.response import AnalyzeResponse
from tools.brand_intelligence.pipeline import (
    BrandIntelligencePipeline,
)
from tools.brand_intelligence.report_generator import (
    HtmlReportGenerator,
)
from backend.config import (
    Settings,
    get_settings,
)
from sqlalchemy.orm import Session

from backend.database.connection import (
    get_database_session,
)
from backend.database.models import (
    BrandAnalysis,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["Analysis"],
)

pipeline = BrandIntelligencePipeline()
report_generator = HtmlReportGenerator()


def get_pipeline() -> BrandIntelligencePipeline:
    return pipeline


def get_report_generator() -> HtmlReportGenerator:
    return report_generator


@router.post(
    "",
    response_model=AnalyzeResponse,
)
async def analyze(
    request: AnalyzeRequest,
    analysis_pipeline: BrandIntelligencePipeline = Depends(
        get_pipeline
    ),
    html_report_generator: HtmlReportGenerator = Depends(
        get_report_generator
    ),
    settings: Settings = Depends(
        get_settings),
    database: Session = Depends(
        get_database_session
    ),
):
    try:
        candidate = analysis_pipeline.analyze_name(
            name=request.name,
            product_description=request.product,
            target_market=request.market,
        )

        output_path = (
            settings.absolute_report_directory
            / f"{candidate.name.lower()}_report.html"
        )

        report_path = html_report_generator.save(
            candidate,
            str(output_path),
        )
        analysis = BrandAnalysis(
        name=candidate.name,
        product_description=request.product,
        target_market=request.market,
        overall_score=candidate.final_score,
        rejected=candidate.rejected,
        report_path=str(report_path),
        status="completed",
        )

        database.add(analysis)
        database.commit()
        database.refresh(analysis)

        return AnalyzeResponse(
            success=True,
            report_path=str(report_path),
            overall_score=candidate.final_score,
            rejected=candidate.rejected,
        )

    except Exception:
        logger.exception(
            "Brand analysis failed for name=%s",
            request.name,
        )

        error_response = ErrorResponse(
            error=ErrorDetail(
                code="ANALYSIS_FAILED",
                message=(
                    "Brand analysis could not be completed."
                ),
            )
        )

        return JSONResponse(
            status_code=500,
            content=error_response.model_dump(),
        )