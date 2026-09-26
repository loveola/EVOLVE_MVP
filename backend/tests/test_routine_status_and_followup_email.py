import uuid
from datetime import datetime, timezone
import importlib.util
from pathlib import Path
import pytest

from app.modules.recommendation.models import UserRoutine
from app.modules.recommendation.schemas import RecommendationResponse, RoutineProgressUpdate, Phase
from app.modules.recommendation.router import _build_recommendation_response
from app.modules.followup.models import Followup
from app.modules.followup.schemas import FollowupResponse


def test_user_routine_status_column_and_default():
    table = UserRoutine.__table__
    assert "status" in table.columns
    assert table.columns["status"].nullable is False
    assert table.columns["status"].type.length == 30

    routine_default = UserRoutine(
        user_id=uuid.uuid4(),
        active_problems=["breakage"],
        cause_explanation_keys=["key1"],
        protocols=["p1"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
    )
    assert routine_default.status == "active"

    routine_custom = UserRoutine(
        user_id=uuid.uuid4(),
        active_problems=["breakage"],
        cause_explanation_keys=["key1"],
        protocols=["p1"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
        status="paused_escalated",
    )
    assert routine_custom.status == "paused_escalated"


def test_followup_user_email_column_and_default():
    table = Followup.__table__
    assert "user_email" in table.columns
    assert table.columns["user_email"].nullable is True
    assert table.columns["user_email"].type.length == 255

    followup_default = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=1,
        due_date=datetime.now(timezone.utc),
    )
    assert followup_default.user_email is None

    followup_with_email = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=1,
        due_date=datetime.now(timezone.utc),
        user_email="curl_user@example.com",
    )
    assert followup_with_email.user_email == "curl_user@example.com"


def test_recommendation_response_status_serialization():
    payload = {
        "user_id": str(uuid.uuid4()),
        "active_problems": [],
        "cause_explanation_keys": [],
        "protocols": [],
        "roadmap": [],
        "product_weight_ceiling": "medium",
        "hard_guards_fired": [],
        "realistic_timeline_weeks": {},
    }
    resp_default = RecommendationResponse(**payload)
    assert resp_default.status == "active"
    assert resp_default.model_dump()["status"] == "active"

    payload_custom = dict(payload, status="paused_escalated")
    resp_custom = RecommendationResponse(**payload_custom)
    assert resp_custom.status == "paused_escalated"
    assert resp_custom.model_dump()["status"] == "paused_escalated"

    assert "status" not in RoutineProgressUpdate.model_fields


def test_followup_response_user_email_serialization():
    f_id = uuid.uuid4()
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    followup_model = Followup(
        id=f_id,
        user_id=u_id,
        routine_id=r_id,
        scheduled_week=2,
        due_date=now,
        status="scheduled",
        user_email="tester@example.com",
    )
    resp = FollowupResponse.model_validate(followup_model)
    assert resp.user_email == "tester@example.com"
    dumped = resp.model_dump()
    assert "user_email" in dumped
    assert dumped["user_email"] == "tester@example.com"

    followup_no_email = Followup(
        id=f_id,
        user_id=u_id,
        routine_id=r_id,
        scheduled_week=2,
        due_date=now,
        status="scheduled",
    )
    resp_no_email = FollowupResponse.model_validate(followup_no_email)
    assert resp_no_email.user_email is None


def test_build_recommendation_response_includes_status():
    routine = UserRoutine(
        user_id=uuid.uuid4(),
        active_problems=[],
        cause_explanation_keys=[],
        protocols=[],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
        is_customized=False,
        status="paused_escalated",
    )
    resp = _build_recommendation_response(routine)
    assert resp.status == "paused_escalated"


def test_migration_011_metadata_and_structure():
    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "011_add_routine_status_and_followup_email.py"
    assert migration_path.exists()
    spec = importlib.util.spec_from_file_location("migration_011", migration_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.revision == "011_add_routine_status_and_followup_email"
    assert mod.down_revision == "010_create_followups"
    assert hasattr(mod, "upgrade")
    assert hasattr(mod, "downgrade")


def test_routine_progress_update_cannot_change_status():
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    from app.modules.auth.dependencies import get_current_user
    from app.modules.auth.schemas import UserResponse

    u_id = uuid.uuid4()
    mock_user = UserResponse(
        uid=str(u_id),
        email="test_status@evolve.com",
        display_name="Status User",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    routine = UserRoutine(
        user_id=u_id,
        active_problems=["breakage"],
        cause_explanation_keys=["key1"],
        protocols=["p1"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
        status="paused_escalated",
    )
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = routine

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.patch(
            "/api/recommendations/me/progress",
            json={"current_phase": 2, "status": "active"},
        )
        assert response.status_code == 200
        assert routine.status == "paused_escalated"
        assert routine.current_phase == 2
    finally:
        app.dependency_overrides.clear()


def test_routine_regeneration_resets_status_to_active():
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.database import get_db
    from app.modules.auth.dependencies import get_current_user
    from app.modules.auth.schemas import UserResponse
    from app.modules.assessment.models import HairAssessment
    from app.modules.recommendation.models import RulesConfig

    u_id = uuid.uuid4()
    mock_user = UserResponse(
        uid=str(u_id),
        email="regen_test@evolve.com",
        display_name="Regen User",
        is_active=True,
        is_admin=False,
        created_at=datetime.now(timezone.utc),
    )
    routine = UserRoutine(
        user_id=u_id,
        active_problems=["breakage"],
        cause_explanation_keys=["key1"],
        protocols=["p1"],
        roadmap=[],
        product_weight_ceiling="medium",
        hard_guards_fired=[],
        realistic_timeline_weeks={},
        status="paused_escalated",
    )
    mock_assessment = HairAssessment(
        id=uuid.uuid4(),
        user_id=u_id,
        answers={},
        results={},
        status="completed",
        created_at=datetime.now(timezone.utc),
    )
    mock_rule = RulesConfig(
        problem_id="breakage",
        display_name="Breakage",
        priority=1,
        is_active=True,
        protocol_id="proto_breakage",
        classifier={"always_true": True},
        score_boosters=[],
        hard_guards=[],
        realistic_timeline_weeks={},
        root_cause_explanation_key="key1",
    )
    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == HairAssessment:
            m.filter.return_value.first.return_value = mock_assessment
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        elif model == RulesConfig:
            m.filter.return_value.all.return_value = [mock_rule]
        elif model == Followup:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "dryness"})
        assert response.status_code == 200
        assert routine.status == "active"
    finally:
        app.dependency_overrides.clear()
