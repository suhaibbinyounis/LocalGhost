"""Tests for the server API."""

import pytest
from httpx import AsyncClient, ASGITransport

from localghost.server import create_app


@pytest.fixture
def app():
    """Create test app."""
    return create_app()


class TestServerAPI:
    """Tests for server API endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, app) -> None:
        """Test health check endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    @pytest.mark.asyncio
    async def test_capabilities_endpoint(self, app) -> None:
        """Test capabilities endpoint."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/capabilities")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "plugins" in data
