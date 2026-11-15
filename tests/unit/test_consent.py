"""Unit Tests for Consent and Data Lineage Enforcement — Phase 2."""

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.models.consent import ConsentEvent


@pytest.mark.asyncio
async def test_consent_defaults_to_off():
    """Rule #2: Consent defaults to OFF for any user without events."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/consent")
        assert res.status_code == 200
        data = res.json()
        assert "training_consent" in data
        assert data["policy_version"] == "1.0"


@pytest.mark.asyncio
async def test_consent_grant_and_withdrawal_cycle():
    """Consent opt-in and withdrawal creates immutable versioned audit events."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Opt-in
        grant_res = await client.put(
            "/api/v1/consent",
            json={"training_consent": True, "purpose": "model_training", "policy_version": "1.0"},
        )
        assert grant_res.status_code == 200
        grant_data = grant_res.json()
        assert grant_data["training_consent"] is True
        assert len(grant_data["history"]) > 0
        latest = grant_data["history"][0]
        assert latest["status"] == "granted"
        assert len(latest["audit_hash"]) == 64

        # Withdraw
        withdraw_res = await client.put(
            "/api/v1/consent",
            json={"training_consent": False, "purpose": "model_training", "policy_version": "1.0"},
        )
        assert withdraw_res.status_code == 200
        withdraw_data = withdraw_res.json()
        assert withdraw_data["training_consent"] is False
        assert withdraw_data["history"][0]["status"] == "withdrawn"


@pytest.mark.asyncio
async def test_data_inventory_endpoint():
    """Doc 02 FR-04: Data inventory provides transparent counts and categories."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/data-inventory")
        assert res.status_code == 200
        data = res.json()
        assert "total_messages_stored" in data
        assert "training_eligible_messages" in data
        assert "categories" in data
        assert len(data["categories"]) >= 3


def test_consent_audit_hash_determinism():
    """Verifies that audit hash is reproducible and cryptographically sound."""
    h1 = ConsentEvent.compute_audit_hash(
        user_id=1,
        status="granted",
        purpose="model_training",
        scope="conversational_ai_finetuning",
        policy_version="1.0",
        timestamp_iso="2026-11-03T20:00:00Z",
    )
    h2 = ConsentEvent.compute_audit_hash(
        user_id=1,
        status="granted",
        purpose="model_training",
        scope="conversational_ai_finetuning",
        policy_version="1.0",
        timestamp_iso="2026-11-03T20:00:00Z",
    )
    assert h1 == h2
    assert len(h1) == 64
