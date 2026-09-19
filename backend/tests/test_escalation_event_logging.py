import uuid
import pytest
from datetime import datetime, timezone
from pathlib import Path
import importlib.util
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment, EscalationEvent
from app.modules.recommendation.models import EscalationFlagConfig
from app.modules.recommendation.escalation import EscalationResult


@pytest.fixture
def mock_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="flagged_user@evolve.com",
        display_name="Flagged User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z"
    )


def test_escalation_event_model_columns():
    table = EscalationEvent.__table__
    assert table.name == "escalation_events"
    columns = {c.name for c in table.columns}
    expected = {
        "id",
        "user_id",
        "assessment_id",
        "flag_code",
        "trigger_reason",
        "timestamp",
        "created_at",
    }
    assert expected.issubset(columns)
    assert table.primary_key.columns.keys() == ["id"]


def test_flagged_submission_creates_escalation_event(mock_user):
    user_uuid = uuid.UUID(mock_user.uid)
    added_instances = []
    stored_assessment = None

    mock_db = MagicMock()

    def mock_add(instance):
        nonlocal stored_assessment
        added_instances.append(instance)
        if isinstance(instance, HairAssessment):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            stored_assessment = instance

    mock_db.add.side_effect = mock_add
    mock_db.query.return_value.filter.return_value.first.side_effect = lambda: stored_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    payload = {
        "answers": {
            "h1_age_bracket": "18_plus",
            "h2_loss_location": ["crown_vertex"],
            "h3_smooth_shiny_no_visible_pores": "yes",
            "h4_scalp_symptoms": ["tingling_crawling"],
            "h5_scalp_lesions": ["none"],
            "g1_primary_concern": ["breakage"],
            "g4_concern_duration": "gt_12m",
            "scalp": "dry",
            "porosity": "takes_over_4_hrs",
            "elasticity": "snaps_immediately",
            "thickness": "medium",
            "density": "medium"
        }
    }

    mock_escalation = EscalationResult(
        tier="RED",
        requires_escalation=True,
        flag_code="RED_01_SCARRING_CENTRAL",
        trigger_reason="Central scalp loss with shiny skin indicates scarring.",
        fired_flags=[{"flag_code": "RED_01_SCARRING_CENTRAL"}]
    )

    try:
        with patch("app.modules.assessment.router.evaluate_escalation", return_value=mock_escalation):
            response = client.post("/api/assessment/submit", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "escalated"
            assert data["results"]["tier"] == "RED"
            assert data["results"]["flag_code"] == "RED_01_SCARRING_CENTRAL"

            events = [x for x in added_instances if isinstance(x, EscalationEvent)]
            assert len(events) == 1
            event = events[0]
            assert event.flag_code == "RED_01_SCARRING_CENTRAL"
            assert len(event.trigger_reason) > 0
            assert event.user_id == user_uuid
            assert event.assessment_id is not None
            assert event.created_at is not None
            assert event.timestamp is not None
            assert mock_db.commit.called
    finally:
        app.dependency_overrides.clear()


def test_non_flagged_submission_does_not_create_escalation_event(mock_user):
    added_instances = []
    stored_assessment = None

    mock_db = MagicMock()

    def mock_add(instance):
        nonlocal stored_assessment
        added_instances.append(instance)
        if isinstance(instance, HairAssessment):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            stored_assessment = instance

    mock_db.add.side_effect = mock_add
    mock_db.query.return_value.filter.return_value.first.side_effect = lambda: stored_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    payload = {
        "answers": {
            "h1_age_bracket": "18_plus",
            "h2_loss_location": ["none"],
            "h3_smooth_shiny_no_visible_pores": "no",
            "h4_scalp_symptoms": ["none"],
            "h5_scalp_lesions": ["none"],
            "g1_primary_concern": ["breakage"],
            "g4_concern_duration": "lt_6m",
            "scalp": "balanced",
            "porosity": "medium",
            "elasticity": "medium",
            "thickness": "medium",
            "density": "medium"
        }
    }

    try:
        response = client.post("/api/assessment/submit", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["results"]["tier"] == "GREEN"

        events = [x for x in added_instances if isinstance(x, EscalationEvent)]
        assert len(events) == 0
    finally:
        app.dependency_overrides.clear()


def test_escalation_logging_persists_even_if_waitlist_abandoned(mock_user):
    user_uuid = uuid.UUID(mock_user.uid)
    added_instances = []
    stored_assessment = None

    mock_db = MagicMock()

    def mock_add(instance):
        nonlocal stored_assessment
        added_instances.append(instance)
        if isinstance(instance, HairAssessment):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            stored_assessment = instance

    mock_db.add.side_effect = mock_add
    mock_db.query.return_value.filter.return_value.first.side_effect = lambda: stored_assessment

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)

    payload = {
        "answers": {
            "h1_age_bracket": "18_plus",
            "h2_loss_location": ["crown_vertex"],
            "h3_smooth_shiny_no_visible_pores": "yes",
            "h4_scalp_symptoms": ["tingling_crawling"],
            "h5_scalp_lesions": ["none"],
            "g1_primary_concern": ["breakage"],
            "g4_concern_duration": "gt_12m"
        }
    }

    mock_escalation = EscalationResult(
        tier="RED",
        requires_escalation=True,
        flag_code="RED_01_SCARRING_CENTRAL",
        trigger_reason="Central scalp loss with shiny skin indicates scarring.",
        fired_flags=[{"flag_code": "RED_01_SCARRING_CENTRAL"}]
    )

    try:
        with patch("app.modules.assessment.router.evaluate_escalation", return_value=mock_escalation):
            response = client.post("/api/assessment/submit", json=payload)
            assert response.status_code == 200

            events = [x for x in added_instances if isinstance(x, EscalationEvent)]
            assert len(events) == 1
            assert events[0].flag_code == "RED_01_SCARRING_CENTRAL"
            assert events[0].user_id == user_uuid
    finally:
        app.dependency_overrides.clear()


def test_migration_007_structure():
    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "007_create_escalation_events.py"
    spec = importlib.util.spec_from_file_location("migration_007", migration_path)
    migration_007 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_007)

    assert migration_007.revision == "007_create_escalation_events"
    assert migration_007.down_revision == "006_create_escalation_flags"
    assert hasattr(migration_007, "upgrade")
    assert hasattr(migration_007, "downgrade")
