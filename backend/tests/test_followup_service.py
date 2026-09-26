import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.modules.assessment.models import HairAssessment
from app.modules.recommendation.models import RulesConfig, UserRoutine
from app.modules.followup.models import Followup
from app.modules.followup.service import (
    schedule_routine_followups,
    dispatch_due_followups,
)
from app.modules.followup.email import (
    send_followup_notification_email,
)


def test_schedule_routine_followups_creates_three_records():
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    started = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    routine = MagicMock(spec=UserRoutine)
    routine.id = r_id
    routine.user_id = u_id
    routine.started_at = started
    routine.created_at = None

    added = []
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []
    mock_db.add.side_effect = lambda x: added.append(x)

    result = schedule_routine_followups(routine, mock_db)

    assert len(result) == 3
    assert len(added) == 3
    mock_db.flush.assert_called_once()

    weeks = [f.scheduled_week for f in result]
    assert weeks == [2, 4, 8]

    for f in result:
        assert f.user_id == u_id
        assert f.routine_id == r_id
        assert f.status == "scheduled"
        expected_due = started + timedelta(weeks=f.scheduled_week)
        assert f.due_date == expected_due


def test_schedule_routine_followups_uses_created_at_fallback():
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    created_at_val = datetime(2026, 9, 10, 8, 0, 0, tzinfo=timezone.utc)
    routine = MagicMock(spec=UserRoutine)
    routine.id = r_id
    routine.user_id = u_id
    routine.started_at = None
    routine.created_at = created_at_val

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = []

    result = schedule_routine_followups(routine, mock_db)
    assert len(result) == 3
    assert result[0].due_date == created_at_val + timedelta(weeks=2)


def test_schedule_routine_followups_idempotency():
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    started = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    routine = MagicMock(spec=UserRoutine)
    routine.id = r_id
    routine.user_id = u_id
    routine.started_at = started
    routine.created_at = None

    existing_followup_2 = MagicMock(spec=Followup)
    existing_followup_2.scheduled_week = 2
    existing_followup_4 = MagicMock(spec=Followup)
    existing_followup_4.scheduled_week = 4
    existing_followup_8 = MagicMock(spec=Followup)
    existing_followup_8.scheduled_week = 8

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [
        existing_followup_2,
        existing_followup_4,
        existing_followup_8,
    ]

    result = schedule_routine_followups(routine, mock_db)
    assert result == []
    mock_db.add.assert_not_called()
    mock_db.flush.assert_called_once()


def test_schedule_routine_followups_partial_existing():
    u_id = uuid.uuid4()
    r_id = uuid.uuid4()
    started = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    routine = MagicMock(spec=UserRoutine)
    routine.id = r_id
    routine.user_id = u_id
    routine.started_at = started
    routine.created_at = None

    existing_followup_2 = MagicMock(spec=Followup)
    existing_followup_2.scheduled_week = 2

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [existing_followup_2]

    result = schedule_routine_followups(routine, mock_db)
    assert len(result) == 2
    weeks = [f.scheduled_week for f in result]
    assert weeks == [4, 8]


def test_dispatch_due_followups_updates_status_and_calls_email():
    now = datetime.now(timezone.utc)
    f1 = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=now - timedelta(days=2),
        status="scheduled",
    )
    f2 = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=4,
        due_date=now - timedelta(hours=1),
        status="due",
    )

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [f1, f2]

    email_calls = []
    def dummy_sender(followup):
        email_calls.append(followup)
        return True

    count = dispatch_due_followups(mock_db, email_sender=dummy_sender)

    assert count == 2
    assert len(email_calls) == 2
    assert f1.status == "sent"
    assert f1.sent_at is not None
    assert f2.status == "sent"
    assert f2.sent_at is not None
    mock_db.commit.assert_called_once()


def test_dispatch_due_followups_without_sender():
    now = datetime.now(timezone.utc)
    f1 = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=now - timedelta(days=1),
        status="scheduled",
    )
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [f1]

    count = dispatch_due_followups(mock_db, email_sender=None)
    assert count == 1
    assert f1.status == "sent"
    assert f1.sent_at is not None
    mock_db.commit.assert_called_once()


def test_dispatch_due_followups_sender_failure_leaves_retryable():
    now = datetime.now(timezone.utc)
    f1 = Followup(
        user_id=uuid.uuid4(),
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=now - timedelta(days=2),
        status="scheduled",
    )
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.all.return_value = [f1]

    def failing_sender(followup):
        return False

    count = dispatch_due_followups(mock_db, email_sender=failing_sender)
    assert count == 0
    assert f1.status == "scheduled"
    assert f1.sent_at is None
    mock_db.commit.assert_called_once()


def test_send_followup_notification_email_missing_key():
    from app.core.config import settings
    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = None
    try:
        with patch("httpx.post") as mock_post:
            res = send_followup_notification_email("user@example.com", "Jane", 2, uuid.uuid4())
            assert res is False
            mock_post.assert_not_called()
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_followup_notification_email_success():
    from app.core.config import settings
    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_key"
    f_id = uuid.uuid4()

    mock_resp = MagicMock()
    mock_resp.status_code = 200

    try:
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            res = send_followup_notification_email("jane@example.com", "Jane Doe", 4, f_id)
            assert res is True
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_key"
            assert call_kwargs["json"]["to"] == ["jane@example.com"]
            assert "Week 4" in call_kwargs["json"]["subject"]
            assert "Jane Doe" in call_kwargs["json"]["html"]
            assert str(f_id) in call_kwargs["json"]["html"]
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_followup_notification_email_html_escaping():
    import html
    from app.core.config import settings
    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_key"
    f_id = uuid.uuid4()
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    try:
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            unsafe_name = "<script>alert('xss')</script> & \"quotes\""
            res = send_followup_notification_email("jane@example.com", unsafe_name, 2, f_id)
            assert res is True
            call_kwargs = mock_post.call_args.kwargs
            expected_escaped = html.escape(unsafe_name)
            assert expected_escaped in call_kwargs["json"]["html"]
            assert "<script>" not in call_kwargs["json"]["html"]
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_followup_notification_email_error_responses():
    import httpx
    from app.core.config import settings
    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_key"
    f_id = uuid.uuid4()

    mock_resp = MagicMock()
    mock_resp.status_code = 500

    try:
        with patch("httpx.post", return_value=mock_resp):
            res = send_followup_notification_email("jane@example.com", "Jane", 2, f_id)
            assert res is False

        with patch("httpx.post", side_effect=httpx.RequestError("Network error")):
            res = send_followup_notification_email("jane@example.com", "Jane", 2, f_id)
            assert res is False
    finally:
        settings.RESEND_API_KEY = orig_key


def test_integration_recommendation_generation_schedules_followups():
    user = UserResponse(
        uid=str(uuid.uuid4()),
        email="routine_sched@evolve.com",
        display_name="Sched User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z"
    )

    mock_assessment = MagicMock()
    mock_assessment.id = uuid.uuid4()
    mock_assessment.status = "completed"
    mock_assessment.results = {"tier": "GREEN"}
    mock_assessment.answers = {
        "q1_treatments": ["none"],
        "q2_heat_frequency": "none",
        "q3_scalp_type": "normal",
        "q4_porosity": "normal",
        "q4_porosity_water_behaviour": "absorbs_normally",
        "q4_drying_time": "1_to_3_hours",
        "q5_elasticity": "low",
        "q6_thickness": "medium",
        "q7_density": "medium",
        "g1_primary_concern": ["dryness"],
        "g2_shed_hair_morphology": "full_length",
        "g4_concern_duration": "months",
        "g5_current_style": "natural_afro",
        "g6_style_tension_pain": "never",
        "g7_install_duration_weeks": 0,
        "g8_wash_interval_days": 7,
        "g9_detangle_method": "wet_conditioner",
        "g10_nighttime_protection": "satin_bonnet",
        "g13_protein_treatment_frequency": "never",
        "g14_hair_state": "natural",
    }

    mock_rule = MagicMock()
    mock_rule.problem_id = "chronic_dryness"
    mock_rule.display_name = "Chronic Dryness"
    mock_rule.classifier = {
        "any_of": [
            {
                "all_of": [
                    {"field": "g1_primary_concern", "contains": "dryness"},
                    {"field": "q5_elasticity", "in": ["low", "healthy"]}
                ]
            }
        ]
    }
    mock_rule.score_boosters = []
    mock_rule.hard_guards = []
    mock_rule.protocol_id = "PROTO_MOISTURE"
    mock_rule.primary_metric = "day3_softness_score"
    mock_rule.root_cause_explanation_key = "cause.dryness"
    mock_rule.realistic_timeline_weeks = {"first_measurable_change": 1}
    mock_rule.always_runs_as_module = False
    mock_rule.priority = 50

    added_objects = []
    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == HairAssessment:
            m.filter.return_value.first.return_value = mock_assessment
        elif model == RulesConfig:
            m.filter.return_value.all.return_value = [mock_rule]
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = None
        elif model == Followup:
            m.filter.return_value.all.return_value = []
        return m

    mock_db.query.side_effect = mock_query
    mock_db.add.side_effect = lambda obj: added_objects.append(obj)

    app.dependency_overrides[get_current_user] = lambda: user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.post("/api/recommendations/generate", json={"concern": "dryness"})
        assert response.status_code == 200
        followup_additions = [obj for obj in added_objects if isinstance(obj, Followup)]
        assert len(followup_additions) == 3
        weeks = sorted([f.scheduled_week for f in followup_additions])
        assert weeks == [2, 4, 8]
    finally:
        app.dependency_overrides.clear()
