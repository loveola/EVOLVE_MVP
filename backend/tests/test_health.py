import os
import pytest
import httpx

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")

@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "Evolve" in data["app"]
