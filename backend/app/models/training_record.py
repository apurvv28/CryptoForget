"""Training Record & Lineage ORM Model — Phase 2."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrainingRecord(Base):
    """
    Lineage tracking record mapping conversation messages to pseudonymous
    training datasets, SISA shards, and slices per Doc 01 (§7) & Doc 05 (§5).
    """
    __tablename__ = "training_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    record_id: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    pseudonymous_subject_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    text_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    is_eligible_for_training: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    consent_event_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("consent_events.id", ondelete="SET NULL"), nullable=True)
    dataset_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    shard_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slice_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_tombstoned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    consent_event = relationship("ConsentEvent", back_populates="training_records")
