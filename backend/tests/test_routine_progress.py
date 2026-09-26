import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.recommendation.models import UserRoutine
from app.modules.recommendation.schemas import RoutineProgressUpdate, RecommendationResponse


@pytest.fixture
def mock_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="routine_user@evolve.com",
        display_name="Routine User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z",
    )


def test_routine_progress_model_columns():
    routine = UserRoutine(
        user_id=uuid.uuid4(),
        active_problems=["dryness"],
        cause_explanation_keys=["cause.dryness"],
        protocols=["PROTO_MOISTURE"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
    )
    assert hasattr(routine, "current_phase")
    assert hasattr(routine, "current_day")
    assert hasattr(routine, "started_at")
    assert hasattr(routine, "completed_actions")
    assert hasattr(routine, "progress_percentage")
    assert routine.current_phase == 1
    assert routine.current_day == 1
    assert routine.started_at is None
    assert routine.completed_actions == []
    assert routine.progress_percentage == 0


def test_routine_progress_update_schema():
    payload = RoutineProgressUpdate(
        current_phase=2,
        current_day=15,
        completed_actions=["action_1", "action_2"],
        progress_percentage=45,
        started_at=datetime(2026, 9, 26, 12, 0, 0, tzinfo=timezone.utc),
    )
    dumped = payload.model_dump(exclude_unset=True)
    assert dumped["current_phase"] == 2
    assert dumped["current_day"] == 15
    assert dumped["completed_actions"] == ["action_1", "action_2"]
    assert dumped["progress_percentage"] == 45
    assert dumped["started_at"] is not None


def test_recommendation_response_schema_has_progress_fields():
    response = RecommendationResponse(
        user_id=str(uuid.uuid4()),
        active_problems=["dryness"],
        cause_explanation_keys=["cause.dryness"],
        protocols=["PROTO_MOISTURE"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
        current_phase=2,
        current_day=10,
        completed_actions=["act1"],
        progress_percentage=25,
    )
    assert response.current_phase == 2
    assert response.current_day == 10
    assert response.completed_actions == ["act1"]
    assert response.progress_percentage == 25
    assert response.started_at is None


def test_migration_009_metadata():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "migration_009",
        "backend/alembic/versions/009_add_routine_progress_tracking.py",
    )
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "009_add_routine_progress_tracking"
    assert mod.down_revision == "008_create_waitlist"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")


def test_patch_progress_unauthenticated():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.patch(
        "/api/recommendations/me/progress",
        json={"current_day": 5},
    )
    assert response.status_code == 401


def test_patch_progress_not_found(mock_user):
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.patch(
            "/api/recommendations/me/progress",
            json={"current_day": 5},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "No active routine found"
    finally:
        app.dependency_overrides.clear()


def test_patch_progress_success(mock_user):
    mock_routine = MagicMock()
    mock_routine.user_id = uuid.UUID(mock_user.uid)
    mock_routine.active_problems = ["chronic_dryness"]
    mock_routine.cause_explanation_keys = ["cause.dryness"]
    mock_routine.protocols = ["PROTO_MOISTURE"]
    mock_routine.roadmap = [
        {
            "phase": 1,
            "name": "Reset & Restore",
            "days": "Day 1 - 14",
            "actions": [{"type": "wash", "instruction": "Hydrating shampoo"}],
            "checkpoint_day": 14,
            "checkpoint_metric": "day3_softness_score",
        }
    ]
    mock_routine.product_weight_ceiling = "medium"
    mock_routine.hard_guards_fired = []
    mock_routine.realistic_timeline_weeks = {"first_measurable_change": 1}
    mock_routine.is_customized = False
    mock_routine.admin_notes = None
    mock_routine.current_phase = 1
    mock_routine.current_day = 1
    mock_routine.started_at = None
    mock_routine.completed_actions = []
    mock_routine.progress_percentage = 0

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_routine

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "current_phase": 1,
            "current_day": 4,
            "completed_actions": ["wash_step_1"],
            "progress_percentage": 20,
            "started_at": now_iso,
        }
        response = client.patch(
            "/api/recommendations/me/progress",
            json=payload,
        )
        assert response.status_code == 200
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_routine)
        assert mock_routine.current_day == 4
        assert mock_routine.completed_actions == ["wash_step_1"]
        assert mock_routine.progress_percentage == 20
        assert mock_routine.started_at is not None
        data = response.json()
        assert data["current_phase"] == 1
        assert data["current_day"] == 4
        assert data["completed_actions"] == ["wash_step_1"]
        assert data["progress_percentage"] == 20
    finally:
        app.dependency_overrides.clear()
