from datetime import datetime, timezone, timedelta
import uuid
import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from config import settings
from core.auth import DEFAULT_FALLBACK_JWT_SECRET
from database import get_db
from main import app
from models.user import User


def create_mock_jwt(user_id: uuid.UUID, email: str = "test@example.com", expired: bool = False, secret: str = None) -> str:
    secret = secret or settings.supabase_jwt_secret or DEFAULT_FALLBACK_JWT_SECRET
    exp = datetime.now(timezone.utc) + (timedelta(seconds=-60) if expired else timedelta(hours=1))
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "exp": exp.timestamp(),
        "user_metadata": {"name": "Test User"},
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.mark.asyncio
async def test_auth_missing_token():
    """Unauthenticated request without overrides should return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_token():
    """Request with invalid signature should return 401."""
    bad_token = create_mock_jwt(uuid.uuid4(), secret="wrong-secret-key-1234567890123456")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_expired_token():
    """Request with expired token should return 401."""
    expired_token = create_mock_jwt(uuid.uuid4(), expired=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_valid_token_auto_sync_user(db_session):
    """Request with valid token for a new user should auto-provision the user."""
    user_id = uuid.uuid4()
    valid_token = create_mock_jwt(user_id, email="newuser@example.com")

    # Mock DB execution returning None initially for user lookup
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {valid_token}"})
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["id"] == str(user_id)
            assert data["email"] == "newuser@example.com"
            assert db_session.add.called
            assert db_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db, None)
