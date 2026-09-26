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

    progress_update = RoutineProgressUpdate(status="paused_escalated")
    assert progress_update.status == "paused_escalated"


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
