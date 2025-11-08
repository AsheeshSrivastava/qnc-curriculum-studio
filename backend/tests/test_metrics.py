import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_request_id_header():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"]


@pytest.mark.asyncio
async def test_metrics_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.get("/api/health")
        response = await client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text




