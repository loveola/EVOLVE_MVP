import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.security import HTTPAuthorizationCredentials
from app.main import app
from app.modules.auth.dependencies import get_current_user



def test_auth_me_without_token():
    client = TestClient(app)
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_get_current_user_user_metadata_cannot_escalate_admin():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy.token")
    mock_payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@evolve.com",
        "role": "authenticated",
        "user_metadata": {"is_admin": True, "role": "admin"},
        "app_metadata": {}
    }

    with patch("jwt.decode", return_value=mock_payload):
        with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
            with patch("app.core.config.settings.SUPABASE_JWT_SECRET", "test-secret"):
                user = await get_current_user(creds)
                assert user.is_admin is False


@pytest.mark.asyncio
async def test_get_current_user_app_metadata_admin_trusted():
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="dummy.token")
    mock_payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "admin@evolve.com",
        "role": "authenticated",
        "user_metadata": {},
        "app_metadata": {"role": "admin"}
    }

    with patch("jwt.decode", return_value=mock_payload):
        with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
            with patch("app.core.config.settings.SUPABASE_JWT_SECRET", "test-secret"):
                user = await get_current_user(creds)
                assert user.is_admin is True


