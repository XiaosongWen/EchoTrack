"""Tests for the /api/v1/users/me endpoint."""

from uuid import UUID
import pytest


@pytest.mark.asyncio
async def test_get_current_user_returns_authenticated_user(client, test_user):
    """GET /api/v1/users/me should return the authenticated user."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"]) == test_user.id
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert "created_at" in data


@pytest.mark.asyncio
async def test_get_current_user_response_shape(client):
    """The response should conform to the UserRead schema."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 200
    data = response.json()["data"]
    assert UUID(data["id"])
    assert isinstance(data["username"], str)
    assert data["email"] is None or isinstance(data["email"], str)


@pytest.mark.asyncio
async def test_user_router_not_found_for_unexpected_path(client):
    """Routes outside /api/v1/users/me should 404 under the users router."""
    response = await client.get("/api/v1/users/999")
    assert response.status_code == 404
