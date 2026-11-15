"""
Deletion Request, Tombstone, and Exclusion Epoch ORM Models — Phase 5 (RC2).

Implements atomic tombstoning, exclusion epochs, and fencing metadata
per Docs 01 (§8, §14), 02 (FR-05, FR-06), and 03 (§4).
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ExclusionEpoch(Base):
    """
    Monotonically increasing epoch counter per dataset scope.
    Every deletion request increments this counter atomically with tombstone creation.
    """
    __tablename__ = "exclusion_epochs"

    scope: Mapped[str] = mapped_column(String(50), primary_key=True, default="default")
    epoch: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)


class DeletionRequest(Base):
    """
    Tracks an asynchronous deletion request through its lifecycle state machine per Doc 01 §9:
    REQUESTED -> AUTHORIZED -> TOMBSTONED -> SOURCE_DELETION -> UNLEARNING_QUEUED ->
    UNLEARNING_RUNNING -> VERIFYING -> COMPLETED
    """
    __tablename__ = "deletion_requests"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"del_{uuid.uuid4().hex[:16]}")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="REQUESTED", nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="all_user_data", nullable=False)
    requested_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    tombstoned_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    exclusion_epoch: Mapped[int | None] = mapped_column(Integer, nullable=True)
    affected_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tombstone_latency_ms: Mapped[float | None] = mapped_column(nullable=True)
    unlearning_time_ms: Mapped[float | None] = mapped_column(nullable=True)
    retrained_model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    affected_shards_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    earliest_affected_slice: Mapped[int | None] = mapped_column(Integer, nullable=True)
    store_checks_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    timeline_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    tombstones = relationship("Tombstone", back_populates="deletion_request", cascade="all, delete-orphan")


class Tombstone(Base):
    """
    Durable, tamper-evident exclusion marker for a specific record.
    Prevents inclusion in any subsequent training dataset or job commit.
    """
    __tablename__ = "tombstones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    deletion_request_id: Mapped[str] = mapped_column(String(64), ForeignKey("deletion_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    record_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    text_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    exclusion_epoch: Mapped[int] = mapped_column(Integer, nullable=False)
    tombstoned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    deletion_request = relationship("DeletionRequest", back_populates="tombstones")
