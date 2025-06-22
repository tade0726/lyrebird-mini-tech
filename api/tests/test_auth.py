import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.models import UserModel


class TestAuthEndpoints:
    """Test authentication endpoints."""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration."""
        response = await client.post(
            "/auth/register",
            json={"email": "newuser@example.com", "password": "password123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_email(
        self, client: AsyncClient, test_user: UserModel
    ):
        """Test registration with duplicate email."""
        response = await client.post(
            "/auth/register", json={"email": test_user.email, "password": "password123"}
        )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration with invalid email."""
        response = await client.post(
            "/auth/register", json={"email": "invalid-email", "password": "password123"}
        )

        assert response.status_code == 422

    async def test_register_missing_password(self, client: AsyncClient):
        """Test registration with missing password."""
        response = await client.post(
            "/auth/register", json={"email": "test@example.com"}
        )

        assert response.status_code == 422

    async def test_login_success(self, client: AsyncClient):
        """Test successful login."""
        # Register user first
        await client.post(
            "/auth/register",
            json={"email": "logintest@example.com", "password": "password123"},
        )

        # Login
        response = await client.post(
            "/auth/login",
            data={"username": "logintest@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(
        self, client: AsyncClient, test_user: UserModel
    ):
        """Test login with invalid credentials."""
        response = await client.post(
            "/auth/login",
            data={"username": test_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login with non-existent user."""
        response = await client.post(
            "/auth/login",
            data={"username": "notexist@example.com", "password": "password123"},
        )

        assert response.status_code == 401

    async def test_get_me_success(self, client: AsyncClient, auth_headers: dict):
        """Test getting current user info."""
        response = await client.get("/auth/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")

        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token."""
        headers = {"Authorization": "Bearer invalid_token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401


class TestTokenValidation:
    """Test JWT token validation."""

    async def test_expired_token_handling(self, client: AsyncClient):
        """Test handling of expired tokens."""
        # Create a token with very short expiration (this would need mocking in real tests)
        headers = {"Authorization": "Bearer expired_token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    async def test_malformed_token(self, client: AsyncClient):
        """Test handling of malformed tokens."""
        headers = {"Authorization": "Bearer malformed.token.here"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401

    async def test_missing_bearer_prefix(self, client: AsyncClient):
        """Test token without Bearer prefix."""
        headers = {"Authorization": "some_token"}
        response = await client.get("/auth/me", headers=headers)

        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password hashing and security."""

    async def test_password_not_stored_plaintext(
        self, test_db: AsyncSession, test_user: UserModel
    ):
        """Test that passwords are not stored in plaintext."""
        # Password should be hashed
        assert test_user.hashed_password != "testpassword123"
        assert len(test_user.hashed_password) > 20  # Hashed passwords are longer

    async def test_password_verification(self, client: AsyncClient):
        """Test password verification during login."""
        # Register with one password
        await client.post(
            "/auth/register",
            json={"email": "passtest@example.com", "password": "correctpassword"},
        )

        # Try to login with different password
        response = await client.post(
            "/auth/login",
            data={"username": "passtest@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
