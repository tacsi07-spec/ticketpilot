from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    app_name: str = "Brand Intelligence API"
    app_version: str = "1.0.0"

    database_url: str = "sqlite:///./ticketpilot.db"
    
    report_directory: Path = Field(
        default=Path(
            "tools/brand_intelligence/reports"
        )
    )

    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def absolute_report_directory(self) -> Path:
        if self.report_directory.is_absolute():
            return self.report_directory

        return (
            PROJECT_ROOT / self.report_directory
        ).resolve()


@lru_cache
def get_settings() -> Settings:
    return Settings()