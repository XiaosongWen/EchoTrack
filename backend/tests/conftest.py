from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import get_current_user
from main import app
from models.user import User

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def test_user():
    """Stub User with UUID for tests."""
    return User(
        id=TEST_USER_ID,
        username="test_user",
        email="test@example.com",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
async def client(test_user):
    """Async HTTP client against the FastAPI app, authenticating as test_user by default."""
    app.dependency_overrides[get_current_user] = lambda: test_user
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def db_session():
    """Mock async session for service-level tests.

    Provides working mocks for add/commit/refresh/execute so services
    that don't need real DB access can be tested in isolation.
    """
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock(return_value=None)

    # Simulate DB flush/refresh: set auto-generated id on new ORM objects
    def _refresh_side_effect(obj):
        if hasattr(obj, "id") and obj.id is None:
            obj.id = uuid4()
        if hasattr(obj, "created_at") and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)
        if hasattr(obj, "updated_at") and obj.updated_at is None:
            obj.updated_at = datetime.now(timezone.utc)
    session.refresh = AsyncMock(side_effect=_refresh_side_effect)

    # Default: execute returns an empty result set (no rows found)
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=result)

    return session
