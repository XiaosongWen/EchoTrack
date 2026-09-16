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


@pytest.mark.asyncio
async def test_auth_es256_token_via_jwks(monkeypatch, db_session):
    """Verify that ES256 tokens signed with EC key are verified via JWKS client."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import core.auth as auth_mod

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    user_id = uuid.uuid4()

    exp = datetime.now(timezone.utc) + timedelta(hours=1)
    payload = {
        "sub": str(user_id),
        "email": "es256user@example.com",
        "role": "authenticated",
        "exp": exp.timestamp(),
        "user_metadata": {"name": "ES256 User"},
    }
    es256_token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-kid"})

    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKSClient:
        def get_signing_key_from_jwt(self, token):
            return MockSigningKey(public_key)

    monkeypatch.setattr(auth_mod, "get_jwks_client", lambda: MockJWKSClient())

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {es256_token}"})
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["id"] == str(user_id)
            assert data["email"] == "es256user@example.com"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_auth_es256_expired_token(monkeypatch):
    """Expired ES256 token returns 401."""
    from cryptography.hazmat.primitives.asymmetric import ec
    import core.auth as auth_mod

    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    user_id = uuid.uuid4()

    exp = datetime.now(timezone.utc) - timedelta(minutes=5)
    payload = {
        "sub": str(user_id),
        "email": "expired@example.com",
        "exp": exp.timestamp(),
    }
    expired_token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-kid"})

    class MockSigningKey:
        def __init__(self, key):
            self.key = key

    class MockJWKSClient:
        def get_signing_key_from_jwt(self, token):
            return MockSigningKey(public_key)

    monkeypatch.setattr(auth_mod, "get_jwks_client", lambda: MockJWKSClient())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401
        assert response.json()["msg"] == "Token has expired"


@pytest.mark.asyncio
async def test_auth_malformed_token_header():
    """Completely malformed token string returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401
