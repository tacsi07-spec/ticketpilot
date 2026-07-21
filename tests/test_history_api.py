import pytest

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.database.connection import (
    Base,
    get_database_session,
)
from backend.database.models import BrandAnalysis


engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

Base.metadata.create_all(
    bind=engine,
)


def override_database_session():
    database = TestingSessionLocal()

    try:
        yield database
    finally:
        database.close()

@pytest.fixture(autouse=True)
def override_database_dependency():
    app.dependency_overrides[
        get_database_session
    ] = override_database_session

    yield

    app.dependency_overrides.pop(
        get_database_session,
        None,
    )

client = TestClient(app)


def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def create_analysis(
    name: str = "Cendora",
) -> BrandAnalysis:
    database = TestingSessionLocal()

    analysis = BrandAnalysis(
        name=name,
        product_description=(
            "AI-powered IT support assistant"
        ),
        target_market=(
            "Germany and European Union"
        ),
        overall_score=8.5,
        rejected=False,
        report_path=f"{name.lower()}_report.html",
        status="completed",
        created_at=datetime.now(timezone.utc),
    )

    database.add(analysis)
    database.commit()
    database.refresh(analysis)
    database.close()

    return analysis


def test_get_history_returns_saved_analyses():
    reset_database()
    create_analysis()

    response = client.get("/history")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Cendora"
    assert data[0]["overall_score"] == 8.5
    assert data[0]["rejected"] is False


def test_get_history_item_returns_analysis():
    reset_database()
    analysis = create_analysis()

    response = client.get(
        f"/history/{analysis.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == analysis.id
    assert response.json()["name"] == "Cendora"


def test_get_history_item_returns_404():
    reset_database()

    response = client.get("/history/999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Analysis not found.",
    }


def test_get_history_respects_limit():
    reset_database()

    create_analysis("Cendora")
    create_analysis("Lumivia")
    create_analysis("Senerva")

    response = client.get(
        "/history?limit=2"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2