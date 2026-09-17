import uuid
import pytest
from pathlib import Path
import importlib.util
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import get_db
from app.modules.waitlist.models import WaitlistEntry


def test_waitlist_model_columns():
    table = WaitlistEntry.__table__
    assert table.name == "waitlist_entries"
    columns = {c.name for c in table.columns}
    expected = {
        "id",
        "email",
        "name",
        "flag_code",
        "notes",
        "created_at",
        "updated_at",
    }
    assert expected.issubset(columns)
    assert table.primary_key.columns.keys() == ["id"]


def test_waitlist_signup_stores_record_and_triggers_email():
    added_instances = []
    mock_db = MagicMock()

    def mock_add(instance):
        if isinstance(instance, WaitlistEntry):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            added_instances.append(instance)

    mock_db.add.side_effect = mock_add

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "flag_code": "RED_01_SCARRING_CENTRAL",
        "notes": "Referred from crown hair loss assessment"
    }

    try:
        with patch("app.modules.waitlist.email.send_waitlist_confirmation_email") as mock_send_email:
            response = client.post("/api/waitlist", json=payload)
            assert response.status_code in [200, 201]
            data = response.json()
            assert data["email"] == "jane@example.com"
            assert data["name"] == "Jane Doe"
            assert data["flag_code"] == "RED_01_SCARRING_CENTRAL"

            assert len(added_instances) == 1
            record = added_instances[0]
            assert record.email == "jane@example.com"
            assert record.name == "Jane Doe"
            assert record.flag_code == "RED_01_SCARRING_CENTRAL"
            assert record.notes == "Referred from crown hair loss assessment"

            mock_send_email.assert_called_once()
            call_kwargs = mock_send_email.call_args.kwargs
            assert call_kwargs.get("email") == "jane@example.com"
            assert call_kwargs.get("name") == "Jane Doe"
    finally:
        app.dependency_overrides.clear()


def test_waitlist_signup_minimal_payload():
    added_instances = []
    mock_db = MagicMock()

    def mock_add(instance):
        if isinstance(instance, WaitlistEntry):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            added_instances.append(instance)

    mock_db.add.side_effect = mock_add

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload = {
        "email": "minimal@example.com"
    }

    try:
        with patch("app.modules.waitlist.email.send_waitlist_confirmation_email") as mock_send_email:
            response = client.post("/api/waitlist", json=payload)
            assert response.status_code in [200, 201]
            data = response.json()
            assert data["email"] == "minimal@example.com"

            assert len(added_instances) == 1
            record = added_instances[0]
            assert record.email == "minimal@example.com"
            assert record.name is None
            assert record.flag_code is None

            mock_send_email.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_waitlist_invalid_email_fails_validation():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload = {
        "email": "invalid-email-string"
    }

    try:
        with patch("app.modules.waitlist.email.send_waitlist_confirmation_email") as mock_send_email:
            response = client.post("/api/waitlist", json=payload)
            assert response.status_code == 422
            mock_send_email.assert_not_called()
    finally:
        app.dependency_overrides.clear()


def test_migration_008_structure():
    migration_path = Path(__file__).parent.parent / "alembic" / "versions" / "008_create_waitlist.py"
    spec = importlib.util.spec_from_file_location("migration_008", migration_path)
    migration_008 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration_008)

    assert migration_008.revision == "008_create_waitlist"
    assert migration_008.down_revision == "007_create_escalation_events"
    assert hasattr(migration_008, "upgrade")
    assert hasattr(migration_008, "downgrade")
