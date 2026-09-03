import os
import pytest
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

@pytest.mark.asyncio
async def test_get_assessment_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/assessment/me")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_save_assessment_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.put("/api/assessment/me", json={"current_step": "A", "answers": {}})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

@pytest.mark.asyncio
async def test_submit_assessment_without_token():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.post("/api/assessment/submit", json={"answers": {}})
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"
