import jwt
import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException
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


@pytest.mark.asyncio
async def test_get_current_user_matching_issuer_succeeds():
    supabase_url = "https://example.supabase.co"
    secret = "test-secret-that-is-at-least-32-bytes-long"
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@evolve.com",
        "aud": "authenticated",
        "iss": f"{supabase_url}/auth/v1",
        "role": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
        with patch("app.core.config.settings.SUPABASE_JWT_SECRET", secret):
            with patch("app.core.config.settings.SUPABASE_URL", supabase_url):
                user = await get_current_user(creds)
                assert user.uid == "11111111-1111-1111-1111-111111111111"
                assert user.email == "user@evolve.com"


@pytest.mark.asyncio
async def test_get_current_user_invalid_issuer_fails():
    supabase_url = "https://example.supabase.co"
    secret = "test-secret-that-is-at-least-32-bytes-long"
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@evolve.com",
        "aud": "authenticated",
        "iss": "https://evil.supabase.co/auth/v1",
        "role": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
        with patch("app.core.config.settings.SUPABASE_JWT_SECRET", secret):
            with patch("app.core.config.settings.SUPABASE_URL", supabase_url):
                with pytest.raises(HTTPException) as exc_info:
                    await get_current_user(creds)
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail == "Invalid or expired Supabase session token."


@pytest.mark.asyncio
async def test_get_current_user_trailing_slash_url_succeeds():
    supabase_url = "https://example.supabase.co/"
    secret = "test-secret-that-is-at-least-32-bytes-long"
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@evolve.com",
        "aud": "authenticated",
        "iss": "https://example.supabase.co/auth/v1",
        "role": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
        with patch("app.core.config.settings.SUPABASE_JWT_SECRET", secret):
            with patch("app.core.config.settings.SUPABASE_URL", supabase_url):
                user = await get_current_user(creds)
                assert user.uid == "11111111-1111-1111-1111-111111111111"
                assert user.email == "user@evolve.com"


@pytest.mark.asyncio
async def test_get_current_user_no_supabase_url_allows_any_issuer():
    secret = "test-secret-that-is-at-least-32-bytes-long"
    payload = {
        "sub": "11111111-1111-1111-1111-111111111111",
        "email": "user@evolve.com",
        "aud": "authenticated",
        "iss": "https://custom.issuer.com/auth/v1",
        "role": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with patch("app.modules.auth.dependencies.get_jwks_client", return_value=None):
        with patch("app.core.config.settings.SUPABASE_JWT_SECRET", secret):
            with patch("app.core.config.settings.SUPABASE_URL", None):
                user = await get_current_user(creds)
                assert user.uid == "11111111-1111-1111-1111-111111111111"




