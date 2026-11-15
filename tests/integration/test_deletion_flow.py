"""
End-to-End Deletion Orchestration Flow Integration Tests — Phase 6.

Validates complete lifecycle transition:
REQUESTED -> AUTHORIZED -> TOMBSTONED -> SOURCE_DELETION -> UNLEARNING_QUEUED ->
UNLEARNING_RUNNING -> VERIFYING -> COMPLETED
per Docs 01 (§9, §14), 02 (FR-05, FR-06, FR-07), 03 (§4), and 05 (§6).
"""

from datetime import datetime, timezone
import uuid
from httpx import ASGITransport, AsyncClient
import pytest
from sqlalchemy import select

from app.db.session import async_session_factory
from app.main import create_app
from app.models.conversation import Conversation, Message
from app.models.deletion import DeletionRequest, Tombstone
from app.models.training_record import TrainingRecord
from app.models.user import User
from app.services.deletion_orchestrator import deletion_orchestrator


@pytest.mark.asyncio
async def test_deletion_flow_unlearning_bypass_when_not_in_training():
    """
    Doc 01 §4: When deleted records were never used in a model, do not run SISA
    unnecessarily. Orchestrator purges raw messages and advances directly through
    verification to COMPLETED.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    user_id_str = uuid.uuid4().hex[:8]
    user_email = f"user_{user_id_str}@example.com"
    username = f"user_{user_id_str}"

    async with async_session_factory() as session:
        user = User(username=username, email=user_email, hashed_password="dummy_hash")
        session.add(user)
        await session.flush()

        conv = Conversation(user_id=user.id, title="Test Deletion Conv")
        session.add(conv)
        await session.flush()

        msg1 = Message(conversation_id=conv.id, role="user", content="My confidential credit card number is 1234-5678")
        msg2 = Message(conversation_id=conv.id, role="assistant", content="I will keep that safe.")
        session.add_all([msg1, msg2])
        await session.commit()
        user_id = user.id

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Request deletion without auto-orchestration first to verify tombstone state
        idem_key = f"idem_{uuid.uuid4().hex[:12]}"
        req_res = await client.post(
            "/api/v1/deletion-requests",
            json={
                "scope": "all_user_data",
                "user_id": user_id,
                "idempotency_key": idem_key,
                "auto_orchestrate": False,
            },
        )
        assert req_res.status_code == 200
        del_data = req_res.json()
        del_id = del_data["deletion_request_id"]
        assert del_data["status"] == "TOMBSTONED"

        # 2. Trigger orchestration synchronously
        orch_res = await client.post(f"/api/v1/deletion-requests/{del_id}/orchestrate?synchronous=true")
        assert orch_res.status_code == 200
        detail = orch_res.json()

        # 3. Verify final state and timeline
        assert detail["status"] == "COMPLETED"
        assert detail["completed_at"] is not None
        assert "mathematical proof" in detail["policy_notice"]

        # Verify store checks
        store_checks = detail["store_checks"]
        assert store_checks["source_data_purged"] is True
        assert store_checks["all_policy_checks_passed"] is True

        # Verify timeline steps
        timeline_statuses = [ev["status"] for ev in detail["timeline"]]
        assert "REQUESTED" in timeline_statuses
        assert "AUTHORIZED" in timeline_statuses
        assert "TOMBSTONED" in timeline_statuses
        assert "SOURCE_DELETION" in timeline_statuses
        assert "UNLEARNING_BYPASS" in timeline_statuses
        assert "VERIFYING" in timeline_statuses
        assert "COMPLETED" in timeline_statuses

    # 4. Verify raw message content in database was redacted
    async with async_session_factory() as session:
        res = await session.execute(select(Message).join(Conversation).where(Conversation.user_id == user_id))
        redacted_msgs = res.scalars().all()
        for m in redacted_msgs:
            assert "[DELETED - PURSUANT TO EXCLUSION REQUEST" in m.content


@pytest.mark.asyncio
async def test_full_deletion_flow_with_sisa_unlearning():
    """
    End-to-End Deletion Orchestration with SISA selective unlearning:
    1. Pre-tombstoning locks the records.
    2. Source messages in SQLite store are redacted.
    3. SISA unlearning retrains only affected shards from slice boundary.
    4. New unlearned model is registered and atomically promoted.
    5. All verification checks pass, leading to COMPLETED state.
    """
    app = create_app()
    transport = ASGITransport(app=app)
    user_id_str = uuid.uuid4().hex[:8]
    user_email = f"user_{user_id_str}@example.com"
    username = f"user_{user_id_str}"

    # Seed user, messages, and training records mapped to shard/slice
    async with async_session_factory() as session:
        user = User(username=username, email=user_email, hashed_password="dummy_hash")
        session.add(user)
        await session.flush()

        conv = Conversation(user_id=user.id, title="Trained Chat")
        session.add(conv)
        await session.flush()

        msg = Message(conversation_id=conv.id, role="user", content="User personal diary text for model training")
        session.add(msg)
        await session.flush()

        # Add training record assigned to shard 0, slice 1 of dataset v1.0-full
        rec_id = f"rec_{uuid.uuid4().hex[:12]}"
        tr = TrainingRecord(
            record_id=rec_id,
            pseudonymous_subject_id=f"subj_{user.id}",
            message_id=msg.id,
            text_digest="sha256_mock_digest",
            is_eligible_for_training=True,
            dataset_version="v1.0-full",
            shard_id=0,
            slice_id=1,
            is_tombstoned=False,
        )
        session.add(tr)
        await session.commit()
        user_id = user.id

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Submit deletion request and run synchronous orchestration
        idem_key = f"idem_full_{uuid.uuid4().hex[:12]}"
        req_res = await client.post(
            "/api/v1/deletion-requests",
            json={
                "scope": "all_user_data",
                "user_id": user_id,
                "idempotency_key": idem_key,
                "auto_orchestrate": False,
            },
        )
        assert req_res.status_code == 200
        del_id = req_res.json()["deletion_request_id"]

        orch_res = await client.post(f"/api/v1/deletion-requests/{del_id}/orchestrate?synchronous=true")
        assert orch_res.status_code == 200
        detail = orch_res.json()

        # Verify orchestration completion
        assert detail["status"] == "COMPLETED"
        assert detail["retrained_model_version"] is not None
        assert "v1.0.del-" in detail["retrained_model_version"]
        assert len(detail["affected_shards"]) > 0
        assert detail["unlearning_time_ms"] is not None and detail["unlearning_time_ms"] > 0

        # Verify all policy verification checks
        assert detail["store_checks"]["all_policy_checks_passed"] is True
        assert detail["store_checks"]["source_data_purged"] is True
        assert detail["store_checks"]["tombstones_active"] is True
        assert detail["store_checks"]["deployment_verified"] is True

        # Fetch status endpoint directly
        status_res = await client.get(f"/api/v1/deletion-requests/{del_id}")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert status_data["status"] == "COMPLETED"
        assert status_data["retrained_model_version"] == detail["retrained_model_version"]
