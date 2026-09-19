import uuid
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import UserResponse
from app.core.database import get_db
from app.modules.recommendation.models import RulesConfig, ProtocolConfig


def _mock_regular_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="user@evolve.com",
        display_name="Regular User",
        is_active=True,
        is_admin=False,
        created_at="2026-09-09T00:00:00Z"
    )


def _mock_admin_user():
    return UserResponse(
        uid=str(uuid.uuid4()),
        email="admin@evolve.com",
        display_name="Admin User",
        is_active=True,
        is_admin=True,
        created_at="2026-09-09T00:00:00Z"
    )


def test_admin_status_unauthenticated():
    app.dependency_overrides.clear()
    client = TestClient(app)
    response = client.get("/api/auth/admin/status")
    assert response.status_code == 401


def test_admin_status_for_regular_user():
    app.dependency_overrides[get_current_user] = _mock_regular_user
    client = TestClient(app)
    try:
        response = client.get("/api/auth/admin/status")
        assert response.status_code == 200
        assert response.json() == {"is_admin": False}
    finally:
        app.dependency_overrides.clear()


def test_admin_status_for_admin_user():
    app.dependency_overrides[get_current_user] = _mock_admin_user
    client = TestClient(app)
    try:
        response = client.get("/api/auth/admin/status")
        assert response.status_code == 200
        assert response.json() == {"is_admin": True}
    finally:
        app.dependency_overrides.clear()


def test_list_rules_forbidden_for_regular_user():
    app.dependency_overrides[get_current_user] = _mock_regular_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    try:
        response = client.get("/api/recommendations/admin/rules")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_rules_for_admin():
    rule = MagicMock()
    rule.problem_id = "chronic_dryness"
    rule.display_name = "Chronic Dryness"
    rule.priority = 50
    rule.is_active = True
    rule.protocol_id = "PROTO_MOISTURE"
    rule.classifier = {}
    rule.score_boosters = []
    rule.hard_guards = []
    rule.realistic_timeline_weeks = {}
    rule.root_cause_explanation_key = "cause.dryness"
    rule.always_runs_as_module = False

    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.all.return_value = [rule]

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.get("/api/recommendations/admin/rules")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["problem_id"] == "chronic_dryness"
    finally:
        app.dependency_overrides.clear()


def test_update_rule_success():
    rule = MagicMock()
    rule.problem_id = "chronic_dryness"
    rule.display_name = "Chronic Dryness"
    rule.priority = 50
    rule.is_active = True
    rule.protocol_id = "PROTO_MOISTURE"
    rule.classifier = {}
    rule.score_boosters = []
    rule.hard_guards = []
    rule.realistic_timeline_weeks = {}
    rule.root_cause_explanation_key = "cause.dryness"
    rule.always_runs_as_module = False

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = rule

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.patch(
            "/api/recommendations/admin/rules/chronic_dryness",
            json={"priority": 80, "is_active": False}
        )
        assert response.status_code == 200
        assert rule.priority == 80
        assert rule.is_active is False
    finally:
        app.dependency_overrides.clear()


def test_update_rule_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.patch(
            "/api/recommendations/admin/rules/non_existent",
            json={"priority": 80}
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_list_protocols_forbidden_for_regular_user():
    app.dependency_overrides[get_current_user] = _mock_regular_user
    app.dependency_overrides[get_db] = lambda: MagicMock()
    client = TestClient(app)
    try:
        response = client.get("/api/recommendations/admin/protocols")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_list_protocols_for_admin():
    proto = MagicMock()
    proto.id = "PROTO_MOISTURE"
    proto.name = "Moisture Protocol"
    proto.problem_id = "chronic_dryness"
    proto.phases = []
    proto.is_active = True

    mock_db = MagicMock()
    mock_db.query.return_value.order_by.return_value.all.return_value = [proto]

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.get("/api/recommendations/admin/protocols")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["id"] == "PROTO_MOISTURE"
    finally:
        app.dependency_overrides.clear()


def test_update_protocol_success():
    proto = MagicMock()
    proto.id = "PROTO_MOISTURE"
    proto.name = "Moisture Protocol"
    proto.problem_id = "chronic_dryness"
    proto.phases = []
    proto.is_active = True

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = proto

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.patch(
            "/api/recommendations/admin/protocols/PROTO_MOISTURE",
            json={"name": "Updated Moisture Protocol", "is_active": False}
        )
        assert response.status_code == 200
        assert proto.name == "Updated Moisture Protocol"
        assert proto.is_active is False
    finally:
        app.dependency_overrides.clear()


def test_update_protocol_not_found():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    app.dependency_overrides[get_current_user] = _mock_admin_user
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)
    try:
        response = client.patch(
            "/api/recommendations/admin/protocols/PROTO_UNKNOWN",
            json={"name": "Unknown"}
        )
        assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()
