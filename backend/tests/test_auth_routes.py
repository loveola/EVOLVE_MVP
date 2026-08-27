import os
import pytest
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

@pytest.mark.asyncio
async def test_auth_me_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/auth/me")
        
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
