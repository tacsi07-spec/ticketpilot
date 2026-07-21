from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from backend.database.connection import (
    get_database_session,
)
from backend.database.models import BrandAnalysis
from backend.schemas.history import HistoryItemResponse


router = APIRouter(
    prefix="/history",
    tags=["history"],
)


@router.get(
    "",
    response_model=list[HistoryItemResponse],
)
def get_history(
    limit: int = 20,
    database: Session = Depends(
        get_database_session
    ),
):
    safe_limit = min(max(limit, 1), 100)

    statement = (
        select(BrandAnalysis)
        .order_by(desc(BrandAnalysis.created_at))
        .limit(safe_limit)
    )

    analyses = database.scalars(
        statement
    ).all()

    return analyses


@router.get(
    "/{analysis_id}",
    response_model=HistoryItemResponse,
)
def get_history_item(
    analysis_id: int,
    database: Session = Depends(
        get_database_session
    ),
):
    analysis = database.get(
        BrandAnalysis,
        analysis_id,
    )

    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found.",
        )

    return analysis