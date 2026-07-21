import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.api.analyze import router as analyze_router
from backend.config import get_settings
from backend.logging_config import configure_logging

from backend.database.connection import (
    Base,
    engine,
)
from backend.database import models

from backend.api.history import (
    router as history_router,
)

settings = get_settings()
configure_logging(settings)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    app: FastAPI,
):
    settings.absolute_report_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    Base.metadata.create_all(
        bind=engine,
    )

    logger.info(
        "Application starting: %s v%s",
        settings.app_name,
        settings.app_version,
    )
    logger.info(
        "Report directory: %s",
        settings.absolute_report_directory,
    )

    yield

    logger.info("Application shutting down")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(analyze_router)
app.include_router(history_router)

@app.get("/")
def root():
    return {
        "message": (
            f"{settings.app_name} is running 🚀"
        )
    }