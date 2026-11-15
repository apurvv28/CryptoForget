"""
Deletion Orchestration & Pre-Tombstoning Service (RC2).

Implements atomic deletion request + tombstone + epoch increment transaction
per Doc 01 (§8, §14), Doc 02 (FR-05, FR-06), and Doc 03 (§4).
"""

from datetime import datetime, timezone
import json
import time
from typing import Any
import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation, Message
from app.models.deletion import DeletionRequest, ExclusionEpoch, Tombstone
from app.models.training_record import TrainingRecord
from app.models.user import User
from app.schemas.deletion import (
    DeletionCreateRequest,
    DeletionDetailResponse,
    DeletionResponse,
    TimelineEvent,
)
from app.services.consent_service import consent_service


class DeletionService:
    """Manages transactional tombstoning and unlearning coordination."""

    async def get_or_create_epoch(self, db: AsyncSession, scope: str = "default") -> ExclusionEpoch:
        """Retrieves or initializes the exclusion epoch record."""
        stmt = select(ExclusionEpoch).where(ExclusionEpoch.scope == scope)
        res = await db.execute(stmt)
        epoch_obj = res.scalar_one_or_none()
        if not epoch_obj:
            epoch_obj = ExclusionEpoch(scope=scope, epoch=1, updated_at=datetime.now(timezone.utc))
            db.add(epoch_obj)
            await db.flush()
        return epoch_obj

    async def get_current_epoch_value(self, db: AsyncSession, scope: str = "default") -> int:
        """Returns the current numerical exclusion epoch."""
        epoch_obj = await self.get_or_create_epoch(db, scope)
        return epoch_obj.epoch

    async def create_deletion_request(
        self,
        request: DeletionCreateRequest,
        db: AsyncSession,
        user_id: int | None = None,
    ) -> DeletionResponse:
        """
        Executes an atomic pre-tombstoning transaction:
        1. Validates or assigns idempotency key.
        2. Increments ExclusionEpoch monotonically.
        3. Marks all matching TrainingRecords as is_tombstoned = True.
        4. Creates durable Tombstone records with the new epoch.
        5. Computes request-to-tombstone latency.
        """
        t0 = time.perf_counter()
        req_timestamp = datetime.now(timezone.utc)

        if not user_id:
            user = await consent_service.get_or_create_default_user(db)
            user_id = user.id

        idempotency_key = request.idempotency_key or f"idem_{uuid.uuid4().hex[:16]}"

        # Idempotency check per Doc 01 §4
        existing_stmt = select(DeletionRequest).where(DeletionRequest.idempotency_key == idempotency_key)
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            return DeletionResponse(
                deletion_request_id=existing.id,
                status=existing.status,
                scope=existing.scope,
                exclusion_epoch=existing.exclusion_epoch or 1,
                affected_records_count=existing.affected_records_count,
                tombstone_latency_ms=existing.tombstone_latency_ms or 0.0,
                requested_at=existing.requested_at,
                tombstoned_at=existing.tombstoned_at,
                policy_notice="Idempotent replay: existing request returned.",
            )

        # 1. Fetch matching messages and training records
        msg_query = (
            select(Message.id)
            .join(Conversation, Message.conversation_id == Conversation.id)
            .where(Conversation.user_id == user_id)
        )
        if request.conversation_ids:
            msg_query = msg_query.where(Conversation.id.in_(request.conversation_ids))

        msg_ids = list((await db.execute(msg_query)).scalars().all())

        tr_stmt = select(TrainingRecord).where(TrainingRecord.message_id.in_(msg_ids)) if msg_ids else None
        target_records = list((await db.execute(tr_stmt)).scalars().all()) if tr_stmt is not None else []

        # 2. Atomic Transaction: Increment Epoch + Commit Tombstones + Insert Request
        epoch_obj = await self.get_or_create_epoch(db)
        epoch_obj.epoch += 1
        epoch_obj.updated_at = datetime.now(timezone.utc)
        new_epoch = epoch_obj.epoch

        del_id = f"del_{uuid.uuid4().hex[:12]}"
        tombstone_time = datetime.now(timezone.utc)

        # Mark records as tombstoned
        for r in target_records:
            r.is_tombstoned = True
            r.is_eligible_for_training = False
            tombstone = Tombstone(
                deletion_request_id=del_id,
                record_id=r.record_id,
                text_digest=r.text_digest,
                exclusion_epoch=new_epoch,
                tombstoned_at=tombstone_time,
            )
            db.add(tombstone)

        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        initial_timeline = [
            {"status": "REQUESTED", "timestamp": req_timestamp.isoformat(), "detail": f"Deletion request initiated for user {user_id}."},
            {"status": "AUTHORIZED", "timestamp": req_timestamp.isoformat(), "detail": f"Request authorized under idempotency key {idempotency_key}."},
            {"status": "TOMBSTONED", "timestamp": tombstone_time.isoformat(), "detail": f"Monotonic exclusion epoch {new_epoch} committed. {len(target_records)} records locked from future processing."},
        ]

        del_record = DeletionRequest(
            id=del_id,
            user_id=user_id,
            idempotency_key=idempotency_key,
            status="TOMBSTONED",
            scope=request.scope,
            requested_at=req_timestamp,
            tombstoned_at=tombstone_time,
            exclusion_epoch=new_epoch,
            affected_records_count=len(target_records),
            tombstone_latency_ms=latency_ms,
            timeline_json=json.dumps(initial_timeline),
            policy_version="1.0",
        )
        db.add(del_record)
        await db.commit()

        # Plain language UX copy per Doc 02 §7
        notice = (
            "Your request has been received. The data has been placed under an exclusion hold. "
            "This does not yet mean model unlearning is complete."
        )

        return DeletionResponse(
            deletion_request_id=del_id,
            status="TOMBSTONED",
            scope=request.scope,
            exclusion_epoch=new_epoch,
            affected_records_count=len(target_records),
            tombstone_latency_ms=latency_ms,
            requested_at=req_timestamp,
            tombstoned_at=tombstone_time,
            policy_notice=notice,
        )

    async def get_deletion_status(self, deletion_id: str, db: AsyncSession) -> DeletionResponse | None:
        """Retrieves basic deletion status."""
        stmt = select(DeletionRequest).where(DeletionRequest.id == deletion_id)
        del_obj = (await db.execute(stmt)).scalar_one_or_none()
        if not del_obj:
            return None

        return DeletionResponse(
            deletion_request_id=del_obj.id,
            status=del_obj.status,
            scope=del_obj.scope,
            exclusion_epoch=del_obj.exclusion_epoch or 1,
            affected_records_count=del_obj.affected_records_count,
            tombstone_latency_ms=del_obj.tombstone_latency_ms or 0.0,
            requested_at=del_obj.requested_at,
            tombstoned_at=del_obj.tombstoned_at,
            policy_notice=del_obj.policy_notice if hasattr(del_obj, "policy_notice") and del_obj.policy_notice else f"Current deletion state: {del_obj.status}",
        )

    async def get_deletion_detail(self, deletion_id: str, db: AsyncSession) -> DeletionDetailResponse | None:
        """Retrieves full deletion lifecycle detail including timeline and store checks."""
        stmt = select(DeletionRequest).where(DeletionRequest.id == deletion_id)
        del_obj = (await db.execute(stmt)).scalar_one_or_none()
        if not del_obj:
            return None

        # Parse timeline
        timeline: list[TimelineEvent] = []
        if del_obj.timeline_json:
            try:
                raw_tl = json.loads(del_obj.timeline_json)
                timeline = [TimelineEvent(**ev) for ev in raw_tl]
            except Exception:
                pass

        # Parse store checks
        store_checks: dict[str, Any] = {}
        if del_obj.store_checks_json:
            try:
                store_checks = json.loads(del_obj.store_checks_json)
            except Exception:
                pass

        # Parse affected shards
        affected_shards: list[int] = []
        if del_obj.affected_shards_json:
            try:
                affected_shards = json.loads(del_obj.affected_shards_json)
            except Exception:
                pass

        # Query certificate if completed
        from app.models.certificate import Certificate
        cert_stmt = select(Certificate.id).where(Certificate.deletion_request_id == deletion_id)
        cert_id = (await db.execute(cert_stmt)).scalar_one_or_none()

        notice = (
            "The deletion workflow completed under policy version 1.0. "
            "The certificate verifies the platform's signed record and the checks listed in it. "
            "It is not a mathematical proof that no model can reproduce any information."
            if del_obj.status == "COMPLETED"
            else f"Current deletion state: {del_obj.status}"
        )

        return DeletionDetailResponse(
            deletion_request_id=del_obj.id,
            status=del_obj.status,
            scope=del_obj.scope,
            exclusion_epoch=del_obj.exclusion_epoch or 1,
            affected_records_count=del_obj.affected_records_count,
            tombstone_latency_ms=del_obj.tombstone_latency_ms or 0.0,
            unlearning_time_ms=del_obj.unlearning_time_ms,
            retrained_model_version=del_obj.retrained_model_version,
            affected_shards=affected_shards,
            earliest_affected_slice=del_obj.earliest_affected_slice,
            store_checks=store_checks,
            timeline=timeline,
            policy_version=del_obj.policy_version or "1.0",
            error_message=del_obj.error_message,
            requested_at=del_obj.requested_at,
            tombstoned_at=del_obj.tombstoned_at,
            completed_at=del_obj.completed_at,
            certificate_id=cert_id,
            policy_notice=notice,
        )


# Global singleton
deletion_service = DeletionService()
