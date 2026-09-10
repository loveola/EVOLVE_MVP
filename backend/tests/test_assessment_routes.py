from fastapi.testclient import TestClient
from app.main import app


def test_get_assessment_without_token():
    client = TestClient(app)
    response = client.get("/api/assessment/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_save_assessment_without_token():
    client = TestClient(app)
    response = client.put("/api/assessment/me", json={"current_step": "A", "answers": {}})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_submit_assessment_without_token():
    client = TestClient(app)
    response = client.post("/api/assessment/submit", json={"answers": {}})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_save_assessment_clears_stale_results():
    import uuid
    from datetime import datetime, timezone
    from unittest.mock import MagicMock
    from app.modules.auth.dependencies import get_current_user
    from app.modules.auth.schemas import UserResponse
    from app.core.database import get_db

    mock_user = UserResponse(
        uid=str(uuid.uuid4()),
        email="user@evolve.com",
        display_name="User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z"
    )

    mock_record = MagicMock()
    mock_record.user_id = uuid.UUID(mock_user.uid)
    mock_record.status = "completed"
    mock_record.results = {"tier": "GREEN"}
    mock_record.current_step = "E"
    mock_record.answers = {"q1": "val"}
    mock_record.updated_at = datetime.now(timezone.utc)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_record

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.put(
            "/api/assessment/me",
            json={"current_step": "B", "answers": {"q1": "updated"}}
        )
        assert response.status_code == 200
        assert mock_record.results is None
        assert mock_record.status == "in_progress"
        assert mock_record.current_step == "B"
    finally:
        app.dependency_overrides.clear()
