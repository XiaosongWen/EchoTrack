"""Tests for the standardized JSON response envelope.

Verifies that every endpoint returns the correct envelope structure:
- Success single: {"msg": "success", "request_id": "...", "data": {...}}
- Success list:   {"msg": "success", "request_id": "...", "data": [...], "pagination": {...}}
- Error:          {"msg": "...", "request_id": "..."}
"""

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import status

from database import get_db
from main import app
from models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _new_commitment(**kwargs):
    """Build a real Commitment ORM object with the given overrides."""
    from models.commitment import Commitment
    defaults = dict(
        id=uuid4(), user_id=uuid4(), type="habit", title="Test",
        description=None, status="active", priority="none",
        config=None, due_date=None, sort_order=0,
        created_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
        updated_at=datetime(2026, 6, 1, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return Commitment(**defaults)


def _new_record(**kwargs):
    """Build a real Record ORM object with the given overrides."""
    from models.record import Record
    defaults = dict(
        id=uuid4(), commitment_id=None, date=date(2026, 6, 15),
        content=None, status="done", value=None, sort_order=0,
        created_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    defaults.update(kwargs)
    return Record(**defaults)


def _assert_single_envelope(body: dict):
    """Assert the body is a valid SingleResponse envelope."""
    assert body["msg"] == "success"
    assert isinstance(body["request_id"], str)
    assert len(body["request_id"]) > 0
    assert "data" in body


def _assert_list_envelope(body: dict):
    """Assert the body is a valid ListResponse envelope."""
    _assert_single_envelope(body)  # shares msg, request_id, data
    assert isinstance(body["data"], list)
    assert "pagination" in body
    pagination = body["pagination"]
    assert isinstance(pagination["page"], int)
    assert isinstance(pagination["page_size"], int)
    assert isinstance(pagination["total_rows"], int)


def _assert_error_envelope(body: dict):
    """Assert the body is a valid ErrorResponse envelope."""
    assert isinstance(body["msg"], str)
    assert len(body["msg"]) > 0
    assert isinstance(body["request_id"], str)
    assert "data" not in body


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    """Override get_db with a mock session.

    Default execute returns empty results. Individual tests override
        ``mock_db.execute`` (via ``return_value`` or ``side_effect``)
        to control what the endpoint receives.
    """
    session = AsyncMock()

    # Default: all queries return empty / not-found
    empty = MagicMock()
    empty.scalar_one_or_none.return_value = None
    empty.scalars.return_value.all.return_value = []
    empty.all.return_value = []
    session.execute = AsyncMock(return_value=empty)

    session.add = MagicMock()
    session.add_all = MagicMock()
    session.commit = AsyncMock(return_value=None)
    session.refresh = AsyncMock(return_value=None)

    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def mock_user_db():
    """Mock session that returns a default User for /users/me."""
    session = AsyncMock()
    default_user = User(
        id=uuid4(), username="default", email=None,
        created_at=datetime.now(timezone.utc),
    )

    async def execute_side_effect(query):
        result = MagicMock()
        result.scalar_one.return_value = default_user
        return result

    session.execute = AsyncMock(side_effect=execute_side_effect)
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# SingleResponse envelope tests
# ---------------------------------------------------------------------------

class TestSingleResponseEnvelope:
    @pytest.mark.asyncio
    async def test_health_envelope(self, client):
        resp = await client.get("/api/v1/health")
        body = resp.json()
        _assert_single_envelope(body)
        assert body["data"] == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_user_me_envelope(self, client, mock_user_db):
        resp = await client.get("/api/v1/users/me")
        body = resp.json()
        _assert_single_envelope(body)
        from uuid import UUID
        assert UUID(body["data"]["id"])

    @pytest.mark.asyncio
    async def test_get_commitment_envelope(self, client, mock_db):
        commitment = _new_commitment(title="Run", type="habit")

        # First query: commitment lookup — needs scalar_one_or_none return
        commit_result = MagicMock()
        commit_result.scalar_one_or_none.return_value = commitment
        # Second query: streak computation — empty dates
        streak_result = MagicMock()
        streak_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [commit_result, streak_result]

        resp = await client.get(f"/api/v1/pursuits/commitments/{commitment.id}")
        body = resp.json()
        _assert_single_envelope(body)
        assert body["data"]["id"] is not None

    @pytest.mark.asyncio
    async def test_create_commitment_envelope(self, client, mock_db):
        def _refresh(obj):
            if obj.id is None:
                obj.id = uuid4()
            if obj.created_at is None:
                obj.created_at = datetime(2026, 6, 1, tzinfo=timezone.utc)
            if obj.updated_at is None:
                obj.updated_at = datetime(2026, 6, 1, tzinfo=timezone.utc)

        mock_db.refresh = AsyncMock(side_effect=_refresh)
        mock_db.execute = AsyncMock(return_value=MagicMock())

        resp = await client.post("/api/v1/pursuits/commitments", json={
            "title": "Run", "type": "habit",
        })
        body = resp.json()
        _assert_single_envelope(body)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_update_commitment_envelope(self, client, mock_db):
        commitment = _new_commitment(title="Run")

        commit_result = MagicMock()
        commit_result.scalar_one_or_none.return_value = commitment
        mock_db.execute = AsyncMock(return_value=commit_result)
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        resp = await client.put(
            f"/api/v1/pursuits/commitments/{commitment.id}",
            json={"title": "Walk"},
        )
        body = resp.json()
        _assert_single_envelope(body)

    @pytest.mark.asyncio
    async def test_create_record_envelope(self, client, mock_db):
        commitment = _new_commitment(type="habit")
        rec_data = _new_record(commitment_id=commitment.id)

        # First execute: commitment lookup → finds commitment
        # Second execute: duplicate check → no duplicate
        commit_result = MagicMock()
        commit_result.scalar_one_or_none.return_value = commitment
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = None
        mock_db.execute.side_effect = [commit_result, dup_result]

        def _refresh(obj):
            if obj.id is None:
                obj.id = uuid4()
            if obj.created_at is None:
                obj.created_at = datetime(2026, 6, 15, tzinfo=timezone.utc)

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock(side_effect=_refresh)

        resp = await client.post("/api/v1/pursuits/records", json={
            "commitment_id": str(commitment.id),
            "date": "2026-06-15",
            "status": "done",
        })
        body = resp.json()
        _assert_single_envelope(body)
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_commitment_progress_envelope(self, client, mock_db):
        """GET commitment returns progress in the response data."""
        commitment = _new_commitment(type="habit")

        # First query: commitment lookup
        commit_result = MagicMock()
        commit_result.scalar_one_or_none.return_value = commitment
        # Second query: streak calculation (empty → streak=0)
        streak_result = MagicMock()
        streak_result.scalars.return_value.all.return_value = []
        mock_db.execute.side_effect = [commit_result, streak_result]

        resp = await client.get(f"/api/v1/pursuits/commitments/{commitment.id}")
        body = resp.json()
        _assert_single_envelope(body)
        assert "progress" in body["data"]

    @pytest.mark.asyncio
    async def test_test_success_envelope(self, client):
        resp = await client.get("/test/success")
        body = resp.json()
        _assert_single_envelope(body)

    @pytest.mark.asyncio
    async def test_test_validation_success_envelope(self, client):
        resp = await client.post("/test/validation-error", json={"name": "x", "value": 1})
        body = resp.json()
        _assert_single_envelope(body)


# ---------------------------------------------------------------------------
# ListResponse envelope tests
# ---------------------------------------------------------------------------

class TestListResponseEnvelope:
    @pytest.mark.asyncio
    async def test_list_commitments_envelope(self, client, mock_db):
        commitments = [_new_commitment(title="Run")]
        commit_result = MagicMock()
        commit_result.scalars.return_value.all.return_value = commitments
        # First execute: list commitments
        # Second execute: batch progress (empty records for habits)
        streak_result = MagicMock()
        streak_result.all.return_value = []
        mock_db.execute.side_effect = [commit_result, streak_result]

        resp = await client.get("/api/v1/pursuits/commitments")
        body = resp.json()
        _assert_list_envelope(body)
        assert body["pagination"]["total_rows"] == 1

    @pytest.mark.asyncio
    async def test_list_commitments_empty_envelope(self, client, mock_db):
        commit_result = MagicMock()
        commit_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=commit_result)

        resp = await client.get("/api/v1/pursuits/commitments")
        body = resp.json()
        _assert_list_envelope(body)
        assert body["pagination"]["total_rows"] == 0

    @pytest.mark.asyncio
    async def test_list_records_envelope(self, client, mock_db):
        record = _new_record()
        record_result = MagicMock()
        record_result.scalars.return_value.all.return_value = [record]
        mock_db.execute = AsyncMock(return_value=record_result)

        resp = await client.get("/api/v1/pursuits/records?from=2026-06-01&to=2026-06-30")
        body = resp.json()
        _assert_list_envelope(body)
        assert body["pagination"]["total_rows"] == 1

    @pytest.mark.asyncio
    async def test_heatmap_envelope(self, client, mock_db):
        heatmap_result = MagicMock()
        heatmap_result.all.return_value = [
            (date(2026, 6, 1), 3),
        ]
        mock_db.execute = AsyncMock(return_value=heatmap_result)

        resp = await client.get("/api/v1/pursuits/heatmap?from=2026-06-01&to=2026-06-30")
        body = resp.json()
        _assert_list_envelope(body)


# ---------------------------------------------------------------------------
# ErrorResponse envelope tests
# ---------------------------------------------------------------------------

class TestErrorResponseEnvelope:
    @pytest.mark.asyncio
    async def test_validation_error_envelope(self, client):
        """POST with invalid data triggers RequestValidationError → error envelope."""
        resp = await client.post("/test/validation-error", json={"name": 123})
        body = resp.json()
        _assert_error_envelope(body)
        assert body["msg"] == "validation_error"

    @pytest.mark.asyncio
    async def test_http_exception_envelope(self, client):
        """GET /test/http-error triggers HTTPException → error envelope."""
        resp = await client.get("/test/http-error")
        assert resp.status_code == 400
        body = resp.json()
        _assert_error_envelope(body)
        assert body["msg"] == "This is an intentional HTTP error"

    @pytest.mark.asyncio
    async def test_server_error_envelope(self, client):
        """GET /test/server-error triggers unhandled exception → error envelope."""
        resp = await client.get("/test/server-error")
        assert resp.status_code == 500
        body = resp.json()
        _assert_error_envelope(body)
        assert body["msg"] == "server_error"

    @pytest.mark.asyncio
    async def test_404_not_found_envelope(self, client, mock_db):
        """GET non-existent commitment → 404 with error envelope.

        The mock_db fixture already returns None from scalar_one_or_none,
        so the service finds nothing and raises 404.
        """
        resp = await client.get(f"/api/v1/pursuits/commitments/{uuid4()}")
        assert resp.status_code == 404
        body = resp.json()
        _assert_error_envelope(body)

    @pytest.mark.asyncio
    async def test_409_conflict_envelope(self, client, mock_db):
        """Duplicate record creation → 409 with error envelope."""
        commitment = _new_commitment(type="habit")

        # First execute: commitment lookup → found
        commit_result = MagicMock()
        commit_result.scalar_one_or_none.return_value = commitment
        # Second execute: duplicate check → existing record found
        dup_result = MagicMock()
        dup_result.scalar_one_or_none.return_value = MagicMock()
        mock_db.execute.side_effect = [commit_result, dup_result]

        resp = await client.post("/api/v1/pursuits/records", json={
            "commitment_id": str(commitment.id),
            "date": "2026-06-15",
            "status": "done",
        })
        assert resp.status_code == 409
        body = resp.json()
        _assert_error_envelope(body)


# ---------------------------------------------------------------------------
# Request-ID consistency tests  (unchanged — use /api/v1/health)
# ---------------------------------------------------------------------------

class TestRequestIdConsistency:
    @pytest.mark.asyncio
    async def test_request_id_in_header_matches_body(self, client):
        """X-Request-ID header should match the request_id in the JSON body."""
        resp = await client.get("/api/v1/health")
        body = resp.json()
        header_id = resp.headers.get("x-request-id")
        assert header_id is not None
        assert header_id == body["request_id"]

    @pytest.mark.asyncio
    async def test_request_ids_are_unique(self, client):
        """Two consecutive requests should get different request_ids."""
        resp1 = await client.get("/api/v1/health")
        resp2 = await client.get("/api/v1/health")
        assert resp1.json()["request_id"] != resp2.json()["request_id"]
