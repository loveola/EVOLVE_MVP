import uuid
from datetime import datetime, timezone
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
    assert table.columns["email"].unique is True


def test_waitlist_signup_stores_record_and_triggers_email():
    added_instances = []
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

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
    mock_db.query.return_value.filter.return_value.first.return_value = None

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


def test_waitlist_signup_normalizes_email_and_trims_whitespace():
    added_instances = []
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    def mock_add(instance):
        if isinstance(instance, WaitlistEntry):
            if not getattr(instance, "id", None):
                instance.id = uuid.uuid4()
            added_instances.append(instance)

    mock_db.add.side_effect = mock_add
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload = {
        "name": "  Jane Doe  ",
        "email": "  JANE.DOE@Example.COM  ",
        "flag_code": "RED_01_SCARRING_CENTRAL"
    }

    try:
        with patch("app.modules.waitlist.email.send_waitlist_confirmation_email") as mock_send_email:
            response = client.post("/api/waitlist", json=payload)
            assert response.status_code in [200, 201]
            data = response.json()
            assert data["email"] == "jane.doe@example.com"
            assert data["name"] == "Jane Doe"
            assert len(added_instances) == 1
            assert added_instances[0].email == "jane.doe@example.com"
            assert added_instances[0].name == "Jane Doe"

            mock_send_email.assert_called_once()
            assert mock_send_email.call_args.kwargs.get("email") == "jane.doe@example.com"
            assert mock_send_email.call_args.kwargs.get("name") == "Jane Doe"
    finally:
        app.dependency_overrides.clear()


def test_waitlist_bounds_validation_excessive_length():
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload_long_name = {
        "email": "valid@example.com",
        "name": "A" * 101
    }
    payload_long_notes = {
        "email": "valid@example.com",
        "notes": "N" * 2001
    }
    payload_long_flag = {
        "email": "valid@example.com",
        "flag_code": "F" * 65
    }

    try:
        r1 = client.post("/api/waitlist", json=payload_long_name)
        assert r1.status_code == 422
        r2 = client.post("/api/waitlist", json=payload_long_notes)
        assert r2.status_code == 422
        r3 = client.post("/api/waitlist", json=payload_long_flag)
        assert r3.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_mask_email_helper():
    from app.modules.waitlist.email import mask_email
    assert mask_email("user@evolve.com") == "u***@evolve.com"
    assert mask_email("jane.doe@example.org") == "j***@example.org"
    assert mask_email("invalid") == "***"


def test_waitlist_signup_duplicate_email_updates_existing_record_and_skips_email():
    mock_db = MagicMock()
    existing_entry = WaitlistEntry(
        id=uuid.uuid4(),
        email="existing@example.com",
        name="Old Name",
        flag_code="OLD_FLAG",
        notes="Old notes",
        created_at=datetime.now(timezone.utc)
    )
    mock_db.query.return_value.filter.return_value.first.return_value = existing_entry

    app.dependency_overrides[get_db] = lambda: mock_db
    client = TestClient(app)

    payload = {
        "email": "Existing@Example.COM",
        "name": "New Name",
        "notes": "Updated notes"
    }

    try:
        with patch("app.modules.waitlist.email.send_waitlist_confirmation_email") as mock_send_email:
            response = client.post("/api/waitlist", json=payload)
            assert response.status_code in [200, 201]
            data = response.json()
            assert data["email"] == "existing@example.com"
            assert data["name"] == "New Name"
            assert data["notes"] == "Updated notes"
            assert data["message"] == "Waitlist entry updated."
            assert existing_entry.name == "New Name"
            assert existing_entry.notes == "Updated notes"
            mock_send_email.assert_not_called()
            mock_db.add.assert_not_called()
            mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.clear()


def test_send_waitlist_confirmation_email_resend_success():
    from app.modules.waitlist.email import send_waitlist_confirmation_email
    from app.core.config import settings

    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_12345"
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "email_123"}

    try:
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = send_waitlist_confirmation_email("jane@example.com", name="Jane")
            assert result is True
            mock_post.assert_called_once()
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["headers"]["Authorization"] == "Bearer re_test_12345"
            assert call_kwargs["json"]["to"] == ["jane@example.com"]
            assert "Jane" in call_kwargs["json"]["text"]
            assert call_kwargs["json"]["subject"] == "You're on the EVOLVE Waitlist"
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_waitlist_confirmation_email_custom_subject_and_body():
    from app.modules.waitlist.email import send_waitlist_confirmation_email
    from app.core.config import settings

    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_12345"
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    try:
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = send_waitlist_confirmation_email(
                "jane@example.com",
                name="Jane",
                custom_subject="Custom Subject",
                custom_body="Custom body text"
            )
            assert result is True
            call_kwargs = mock_post.call_args.kwargs
            assert call_kwargs["json"]["subject"] == "Custom Subject"
            assert call_kwargs["json"]["text"] == "Custom body text"
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_waitlist_confirmation_email_missing_key_skips_cleanly():
    from app.modules.waitlist.email import send_waitlist_confirmation_email
    from app.core.config import settings

    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = None

    try:
        with patch("httpx.post") as mock_post:
            result = send_waitlist_confirmation_email("jane@example.com", name="Jane")
            assert result is True
            mock_post.assert_not_called()
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_waitlist_confirmation_email_resend_api_error_returns_false():
    from app.modules.waitlist.email import send_waitlist_confirmation_email
    from app.core.config import settings

    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_12345"
    mock_resp = MagicMock()
    mock_resp.status_code = 422

    try:
        with patch("httpx.post", return_value=mock_resp) as mock_post:
            result = send_waitlist_confirmation_email("jane@example.com", name="Jane")
            assert result is False
            mock_post.assert_called_once()
    finally:
        settings.RESEND_API_KEY = orig_key


def test_send_waitlist_confirmation_email_network_exception_returns_false():
    import httpx
    from app.modules.waitlist.email import send_waitlist_confirmation_email
    from app.core.config import settings

    orig_key = settings.RESEND_API_KEY
    settings.RESEND_API_KEY = "re_test_12345"

    try:
        with patch("httpx.post", side_effect=httpx.ConnectError("Network down")):
            result = send_waitlist_confirmation_email("jane@example.com", name="Jane")
            assert result is False
    finally:
        settings.RESEND_API_KEY = orig_key
