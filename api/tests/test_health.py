import pytest
from httpx import AsyncClient


class TestHealthEndpoints:
    """Test health check and basic endpoints."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Lyrebird API" in data["message"]

    @pytest.mark.asyncio
    async def test_openapi_docs_available(self, client: AsyncClient):
        """Test that OpenAPI docs are available."""
        response = await client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert data["info"]["title"] == "Lyrebird Mini Tech API"

    @pytest.mark.asyncio
    async def test_docs_endpoint_available(self, client: AsyncClient):
        """Test that documentation endpoint is available."""
        response = await client.get("/docs")

        # Docs endpoint should return HTML
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    @pytest.mark.asyncio
    async def test_redoc_endpoint_available(self, client: AsyncClient):
        """Test that ReDoc endpoint is available."""
        response = await client.get("/redoc")

        # ReDoc endpoint should return HTML
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
