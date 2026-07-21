from pathlib import Path

from fastapi.testclient import TestClient

from backend.api.analyze import (
    get_pipeline,
    get_report_generator,
)
from backend.app import app

from backend.config import (
    Settings,
    get_settings,
)

client = TestClient(app)


class FakeCandidate:
    name = "Cendora"
    final_score = 9.3
    rejected = False


class FakePipeline:
    def analyze_name(
        self,
        name: str,
        product_description: str,
        target_market: str,
    ) -> FakeCandidate:
        assert name == "Cendora"
        assert product_description == (
            "AI-powered IT support assistant"
        )
        assert target_market == (
            "Germany and European Union"
        )

        return FakeCandidate()


class FakeReportGenerator:
    def save(
        self,
        candidate: FakeCandidate,
        output_path: str,
    ) -> Path:
        assert candidate.name == "Cendora"
        assert output_path.endswith(
            "cendora_report.html"
        )

        return Path(
            "tools/brand_intelligence/reports/"
            "cendora_report.html"
        )

def get_test_settings() -> Settings:
    return Settings(
        report_directory=(
            "tools/brand_intelligence/reports"
        ),
        _env_file=None,
    )

def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Brand Intelligence API is running 🚀"
    }


def test_analyze_validation():
    response = client.post(
        "/analyze",
        json={
            "name": "-",
            "product": "short",
            "market": "Germany",
        },
    )

    assert response.status_code == 422


def test_analyze_success_with_mocked_dependencies():
    app.dependency_overrides[get_pipeline] = (
        lambda: FakePipeline()
    )
    app.dependency_overrides[get_report_generator] = (
        lambda: FakeReportGenerator()
    )
    app.dependency_overrides[get_settings] = (
        get_test_settings
    )

    try:
        response = client.post(
            "/analyze",
            json={
                "name": "Cendora",
                "product": (
                    "AI-powered IT support assistant"
                ),
                "market": (
                    "Germany and European Union"
                ),
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["overall_score"] == 9.3
    assert data["rejected"] is False
    assert data["report_path"].endswith("cendora_report.html")

class FailingPipeline:
   def analyze_name(
        self,
        name: str,
        product_description: str,
        target_market: str,
    ):
        raise RuntimeError("Sensitive internal error")


def test_analyze_returns_safe_error_response():
    app.dependency_overrides[get_pipeline] = (
        lambda: FailingPipeline()
    )
    app.dependency_overrides[get_report_generator] = (
        lambda: FakeReportGenerator()
    )

    try:
        response = client.post(
            "/analyze",
            json={
                "name": "Cendora",
                "product": "AI-powered IT support assistant",
                "market": "Germany and European Union",
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 500
    assert response.json() == {
        "success": False,
        "error": {
            "code": "ANALYSIS_FAILED",
            "message": (
                "Brand analysis could not be completed."
            ),
        },
    }
    assert "Sensitive internal error" not in response.text     