"""Tests for the Pydantic UserRead schema."""

from datetime import datetime, timezone
import uuid

from schemas.user import UserRead


class TestUserReadSchema:
    """UserRead serialisation and validation."""

    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()
        user_data = {"id": user_id, "username": "default", "email": None, "created_at": now}
        schema = UserRead.model_validate(user_data)
        assert schema.id == user_id
        assert schema.username == "default"
        assert schema.email is None
        assert schema.created_at == now

    def test_from_attributes_with_email(self):
        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()
        user_data = {
            "id": user_id,
            "username": "alice",
            "email": "alice@example.com",
            "created_at": now,
        }
        schema = UserRead.model_validate(user_data)
        assert schema.email == "alice@example.com"
        assert schema.id == user_id

    def test_json_serialisation(self):
        now = datetime.now(timezone.utc)
        user_id = uuid.uuid4()
        user_data = {"id": user_id, "username": "default", "email": None, "created_at": now}
        schema = UserRead.model_validate(user_data)
        dumped = schema.model_dump()
        assert dumped["id"] == user_id
        assert dumped["username"] == "default"
        assert dumped["email"] is None
        assert "created_at" in dumped
