"""Unit Tests for Atomic Pre-Tombstoning — Phase 5 (RC2)."""

import uuid
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app


@pytest.mark.asyncio
async def test_tombstone_created_atomically_with_request():
    """Doc 01 §8: Deletion request creates tombstones and increments exclusion epoch."""
    app = create_app()
    transport = ASGITransport(app=app)
    idem_key = f"test_idem_{uuid.uuid4().hex[:8]}"

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Fetch current epoch
        epoch_res = await client.get("/api/v1/deletion-requests/epoch/current")
        assert epoch_res.status_code == 200
        start_epoch = epoch_res.json()["epoch"]

        # 2. Submit deletion request
        del_res = await client.post(
            "/api/v1/deletion-requests",
            json={"scope": "all_user_data", "idempotency_key": idem_key},
        )
        assert del_res.status_code == 200
        data = del_res.json()
        assert data["status"] == "TOMBSTONED"
        assert data["exclusion_epoch"] == start_epoch + 1
        assert data["tombstone_latency_ms"] >= 0.0

        # 3. Check idempotency: second call with same key returns identical request
        idem_res = await client.post(
            "/api/v1/deletion-requests",
            json={"scope": "all_user_data", "idempotency_key": idem_key},
        )
        assert idem_res.status_code == 200
        idem_data = idem_res.json()
        assert idem_data["deletion_request_id"] == data["deletion_request_id"]
        assert idem_data["exclusion_epoch"] == data["exclusion_epoch"]
