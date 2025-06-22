import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api.main import app
from api.database import get_session, Base
from api.models import UserModel
from api.utils.security import get_password_hash


# Test database URL (SQLite in memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async with TestSessionLocal() as session:
        yield session

    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database dependency override."""

    def override_get_session():
        return test_db

    app.dependency_overrides[get_session] = override_get_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user(test_db: AsyncSession) -> UserModel:
    """Create a test user."""
    user = UserModel(
        email="test@example.com", hashed_password=get_password_hash("testpassword123")
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_token(client: AsyncClient) -> str:
    """Get authentication token for test user."""
    # Register user
    await client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "testpassword123"},
    )

    # Login and get token
    response = await client.post(
        "/auth/login",
        data={"username": "test@example.com", "password": "testpassword123"},
    )

    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict:
    """Get authorization headers with token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def sample_audio_data() -> bytes:
    """Create sample audio data for testing."""
    # Create a minimal WAV file header + some dummy data
    wav_header = (
        b"RIFF"
        b"\x24\x00\x00\x00"  # File size
        b"WAVE"
        b"fmt "
        b"\x10\x00\x00\x00"  # Format chunk size
        b"\x01\x00"  # Audio format (PCM)
        b"\x01\x00"  # Number of channels
        b"\x44\xac\x00\x00"  # Sample rate (44100)
        b"\x88\x58\x01\x00"  # Byte rate
        b"\x02\x00"  # Block align
        b"\x10\x00"  # Bits per sample
        b"data"
        b"\x00\x00\x00\x00"  # Data chunk size
    )
    # Add some dummy audio data
    dummy_data = b"\x00" * 100
    return wav_header + dummy_data
