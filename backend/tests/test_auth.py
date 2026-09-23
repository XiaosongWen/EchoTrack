from datetime import datetime, timezone, timedelta
import uuid
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import ASGITransport, AsyncClient

from database import get_db
from main import app
from models.user import User
import core.auth as auth_mod

# EC key pair shared across all tests in this module.
# create_mock_jwt signs with _PRIVATE_KEY; mock_jwks makes verify_jwt resolve it.
_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
_PUBLIC_KEY = _PRIVATE_KEY.public_key()
_WRONG_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())  # different key → invalid sig


def create_mock_jwt(
    user_id: uuid.UUID,
    email: str = "test@example.com",
    expired: bool = False,
    private_key=None,
) -> str:
    """Mint an ES256 JWT signed with the test EC private key (or a supplied one)."""
    key = private_key or _PRIVATE_KEY
    exp = datetime.now(timezone.utc) + (timedelta(seconds=-60) if expired else timedelta(hours=1))
    payload = {
        "sub": str(user_id),
        "email": email,
        "role": "authenticated",
        "exp": exp.timestamp(),
        "user_metadata": {"name": "Test User"},
    }
    return jwt.encode(payload, key, algorithm="ES256", headers={"kid": "test-kid"})


class _MockSigningKey:
    def __init__(self, key):
        self.key = key


class _MockJWKSClient:
    """Returns the shared test public key for any token."""
    def get_signing_key_from_jwt(self, token):
        return _MockSigningKey(_PUBLIC_KEY)


@pytest.fixture
def mock_jwks(monkeypatch):
    """Patch get_jwks_client so verify_jwt resolves ES256 tokens without a real Supabase URL."""
    monkeypatch.setattr(auth_mod, "get_jwks_client", lambda: _MockJWKSClient())




@pytest.mark.asyncio
async def test_auth_missing_token():
    """Unauthenticated request without overrides should return 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me")
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_invalid_token(mock_jwks):
    """Token signed with a different EC key should return 401."""
    bad_token = create_mock_jwt(uuid.uuid4(), private_key=_WRONG_PRIVATE_KEY)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {bad_token}"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_expired_token(mock_jwks):
    """Request with expired token should return 401."""
    expired_token = create_mock_jwt(uuid.uuid4(), expired=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
        assert response.status_code == 401


@pytest.mark.asyncio
async def test_auth_valid_token_auto_sync_user(mock_jwks, db_session):
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
async def test_auth_es256_token_via_jwks(mock_jwks, db_session):
    """ES256 tokens signed with EC key are verified via JWKS client."""
    user_id = uuid.uuid4()
    token = create_mock_jwt(user_id, email="es256user@example.com")

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["id"] == str(user_id)
            assert data["email"] == "es256user@example.com"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_auth_es256_expired_token(mock_jwks):
    """Expired ES256 token returns 401."""
    expired_token = create_mock_jwt(uuid.uuid4(), email="expired@example.com", expired=True)
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


@pytest.mark.asyncio
async def test_auth_concurrent_user_creation_integrity_error(mock_jwks, db_session):
    """When concurrent requests attempt to insert the user, IntegrityError is caught and existing user returned."""
    from unittest.mock import MagicMock
    from sqlalchemy.exc import IntegrityError

    user_id = uuid.uuid4()
    valid_token = create_mock_jwt(user_id, email="concurrent@example.com")
    existing_user = User(
        id=user_id,
        email="concurrent@example.com",
        username="concurrent",
        created_at=datetime.now(timezone.utc),
    )

    # First commit fails with IntegrityError (duplicate key race)
    db_session.commit.side_effect = [IntegrityError("duplicate key", params=None, orig=Exception("UniqueViolationError")), None]

    # After rollback, second execute returns the existing user
    mock_result_first = MagicMock()
    mock_result_first.scalar_one_or_none.return_value = None

    mock_result_second = MagicMock()
    mock_result_second.scalar_one_or_none.return_value = existing_user

    db_session.execute.side_effect = [mock_result_first, mock_result_second]

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/users/me", headers={"Authorization": f"Bearer {valid_token}"})
            assert response.status_code == 200
            data = response.json()["data"]
            assert data["id"] == str(user_id)
            assert db_session.rollback.called
    finally:
        app.dependency_overrides.pop(get_db, None)
        db_session.commit.side_effect = None
        db_session.execute.side_effect = None
