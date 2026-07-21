from pathlib import Path

from backend.config import (
    PROJECT_ROOT,
    Settings,
    get_settings,
)


def test_settings_have_default_values():
    settings = Settings(
        _env_file=None,
    )

    assert settings.app_name == (
        "Brand Intelligence API"
    )
    assert settings.app_version == "1.0.0"
    assert settings.log_level == "INFO"


def test_relative_report_directory_becomes_absolute():
    settings = Settings(
        report_directory=Path(
            "custom/reports"
        ),
        _env_file=None,
    )

    expected = (
        PROJECT_ROOT / "custom/reports"
    ).resolve()

    assert (
        settings.absolute_report_directory
        == expected
    )


def test_absolute_report_directory_is_preserved(
    tmp_path: Path,
):
    settings = Settings(
        report_directory=tmp_path,
        _env_file=None,
    )

    assert (
        settings.absolute_report_directory
        == tmp_path
    )


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    first = get_settings()
    second = get_settings()

    assert first is second

    get_settings.cache_clear()