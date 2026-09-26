import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.followup.models import Followup
from app.modules.recommendation.models import UserRoutine
from app.modules.assessment.models import EscalationEvent


@pytest.fixture
def mock_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="user@evolve.com",
        display_name="Followup User",
        is_active=True,
        created_at="2026-09-09T00:00:00Z",
    )


def test_followups_me_unauthenticated():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.get("/api/followups/me")
    assert response.status_code == 401


def test_followups_me_authenticated_returns_ordered_list(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    f1 = Followup(
        id=uuid.uuid4(),
        user_id=user_id,
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )
    f2 = Followup(
        id=uuid.uuid4(),
        user_id=user_id,
        routine_id=uuid.uuid4(),
        scheduled_week=4,
        due_date=datetime(2026, 9, 29, tzinfo=timezone.utc),
        status="scheduled",
    )

    mock_db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    order_mock = MagicMock()

    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.order_by.return_value = order_mock
    order_mock.all.return_value = [f1, f2]

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get("/api/followups/me")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["scheduled_week"] == 2
        assert data[1]["scheduled_week"] == 4
    finally:
        app.dependency_overrides.clear()


def test_followups_me_next_returns_earliest_upcoming(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    f1 = Followup(
        id=uuid.uuid4(),
        user_id=user_id,
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )

    mock_db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    order_mock = MagicMock()

    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.order_by.return_value = order_mock
    order_mock.first.return_value = f1

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get("/api/followups/me/next")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(f1.id)
        assert data["scheduled_week"] == 2
    finally:
        app.dependency_overrides.clear()


def test_followups_me_next_returns_404_when_none(mock_user):
    mock_db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    order_mock = MagicMock()

    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.order_by.return_value = order_mock
    order_mock.first.return_value = None

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        response = client.get("/api/followups/me/next")
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_check_in_improving_advances_phase(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )

    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 1
    routine.assessment_id = uuid.uuid4()
    routine.roadmap = [
        {"phase": 1, "name": "Phase 1"},
        {"phase": 2, "name": "Phase 2"},
        {"phase": 3, "name": "Phase 3"},
        {"phase": 4, "name": "Phase 4"},
    ]

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "improving",
            "response_notes": "Hair feels much softer",
            "response_symptoms": [],
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] == "advanced_phase"
        assert data["escalated"] is False
        assert data["current_phase"] == 2
        assert routine.current_phase == 2
        assert followup.status == "completed"
        assert followup.completed_at is not None
        assert followup.response_rating == "improving"
        assert followup.action_taken == "advanced_phase"
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_check_in_no_change_advances_phase(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )

    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 1
    routine.assessment_id = uuid.uuid4()
    routine.roadmap = [
        {"phase": 1, "name": "Phase 1"},
        {"phase": 2, "name": "Phase 2"},
    ]

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "no_change",
            "response_notes": "Holding steady",
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] == "advanced_phase"
        assert data["escalated"] is False
        assert data["current_phase"] == 2
        assert routine.current_phase == 2
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_check_in_worse_logs_escalation_event(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()
    assessment_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )

    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 1
    routine.assessment_id = assessment_id
    routine.roadmap = [{"phase": 1, "name": "Phase 1"}]

    added = []
    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query
    mock_db.add.side_effect = lambda obj: added.append(obj)

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "worse",
            "response_notes": "Increased breakage noticed",
            "response_symptoms": ["excessive_shedding"],
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] == "escalated"
        assert data["escalated"] is True
        assert data["escalation_advisory"] is not None
        assert routine.current_phase == 1

        escalations = [x for x in added if isinstance(x, EscalationEvent)]
        assert len(escalations) == 1
        assert escalations[0].user_id == user_id
        assert escalations[0].flag_code == "CHECKIN_ESCALATION"
        assert escalations[0].assessment_id == assessment_id
        assert escalations[0].trigger_reason == "Check-in Week 2 reported worse with symptoms: excessive_shedding"
        assert followup.status == "completed"
        assert followup.action_taken == "escalated"
        mock_db.commit.assert_called()
    finally:
        app.dependency_overrides.clear()


def test_check_in_severe_reaction_logs_severe_reaction_event(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=4,
        due_date=datetime(2026, 9, 29, tzinfo=timezone.utc),
        status="scheduled",
    )

    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 1
    routine.assessment_id = None
    routine.roadmap = []

    added = []
    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query
    mock_db.add.side_effect = lambda obj: added.append(obj)

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "severe_reaction",
            "response_notes": "Scalp burning and hives",
            "response_symptoms": ["burning", "hives"],
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] == "escalated"
        assert data["escalated"] is True
        assert routine.current_phase == 1

        escalations = [x for x in added if isinstance(x, EscalationEvent)]
        assert len(escalations) == 1
        assert escalations[0].user_id == user_id
        assert escalations[0].flag_code == "SEVERE_REACTION"
        assert escalations[0].trigger_reason == "Check-in Week 4 reported severe_reaction with symptoms: burning, hives"
    finally:
        app.dependency_overrides.clear()


def test_check_in_already_completed_returns_400(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="completed",
        completed_at=datetime.now(timezone.utc),
    )

    mock_db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = followup

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {"response_rating": "improving"}
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 400
        assert "completed" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_check_in_other_user_followup_returns_404(mock_user):
    other_user_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=other_user_id,
        routine_id=uuid.uuid4(),
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )

    mock_db = MagicMock()
    query_mock = MagicMock()
    filter_mock = MagicMock()
    mock_db.query.return_value = query_mock
    query_mock.filter.return_value = filter_mock
    filter_mock.first.return_value = followup

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {"response_rating": "improving"}
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_check_in_invalid_rating_returns_422(mock_user):
    followup_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        payload = {"response_rating": "great"}
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_check_in_worse_without_symptoms_trigger_reason(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )
    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 1
    routine.assessment_id = None
    routine.roadmap = []

    added = []
    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query
    mock_db.add.side_effect = lambda obj: added.append(obj)

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "worse",
            "response_notes": "Slightly worse",
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        escalations = [x for x in added if isinstance(x, EscalationEvent)]
        assert len(escalations) == 1
        assert escalations[0].trigger_reason == "Check-in Week 2 reported worse"
    finally:
        app.dependency_overrides.clear()


def test_check_in_maintained_at_max_phase(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()

    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=4,
        due_date=datetime(2026, 9, 29, tzinfo=timezone.utc),
        status="scheduled",
    )
    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.current_phase = 3
    routine.assessment_id = None
    routine.roadmap = [
        {"phase": 1, "name": "Phase 1"},
        {"phase": 2, "name": "Phase 2"},
        {"phase": 3, "name": "Phase 3"},
    ]

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {"response_rating": "improving"}
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["action_taken"] == "maintained"
        assert data["message"] == "Routine maintained at maximum phase."
        assert data["current_phase"] == 3
        assert routine.current_phase == 3
    finally:
        app.dependency_overrides.clear()


def test_check_in_notes_too_long_returns_422(mock_user):
    followup_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "improving",
            "response_notes": "a" * 2001,
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_check_in_symptoms_too_many_returns_422(mock_user):
    followup_id = uuid.uuid4()
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "improving",
            "response_symptoms": ["itching"] * 51,
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_check_in_worse_pauses_routine(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()
    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )
    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.status = "active"
    routine.current_phase = 1
    routine.assessment_id = None
    routine.roadmap = []

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "worse",
            "response_notes": "Breakage worsening",
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        assert routine.status == "paused_escalated"
    finally:
        app.dependency_overrides.clear()


def test_check_in_severe_reaction_pauses_routine(mock_user):
    user_id = uuid.UUID(mock_user.uid)
    routine_id = uuid.uuid4()
    followup_id = uuid.uuid4()
    followup = Followup(
        id=followup_id,
        user_id=user_id,
        routine_id=routine_id,
        scheduled_week=2,
        due_date=datetime(2026, 9, 15, tzinfo=timezone.utc),
        status="scheduled",
    )
    routine = MagicMock(spec=UserRoutine)
    routine.id = routine_id
    routine.user_id = user_id
    routine.status = "active"
    routine.current_phase = 1
    routine.assessment_id = None
    routine.roadmap = []

    mock_db = MagicMock()
    def mock_query(model):
        m = MagicMock()
        if model == Followup:
            m.filter.return_value.first.return_value = followup
        elif model == UserRoutine:
            m.filter.return_value.first.return_value = routine
        return m

    mock_db.query.side_effect = mock_query

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    try:
        payload = {
            "response_rating": "improving",
            "response_symptoms": ["severe_burning"],
        }
        response = client.post(f"/api/followups/{followup_id}/check-in", json=payload)
        assert response.status_code == 200
        assert routine.status == "paused_escalated"
    finally:
        app.dependency_overrides.clear()

