"""Consent Event ORM Model — Phase 2."""

from datetime import datetime, timezone
import hashlib
from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ConsentEvent(Base):
    """
    Immutable audit trail of consent events per Doc 02 FR-03 & Doc 05 §3.
    Records every grant and withdrawal with policy version and tamper-evident audit hash.
    """
    __tablename__ = "consent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # "granted" | "withdrawn"
    purpose: Mapped[str] = mapped_column(String(100), default="model_training", nullable=False)
    scope: Mapped[str] = mapped_column(String(100), default="conversational_ai_finetuning", nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    effective_timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    audit_hash: Mapped[str] = mapped_column(String(64), nullable=False)

    user = relationship("User", back_populates="consent_events")
    training_records = relationship("TrainingRecord", back_populates="consent_event")

    @staticmethod
    def compute_audit_hash(
        user_id: int,
        status: str,
        purpose: str,
        scope: str,
        policy_version: str,
        timestamp_iso: str,
    ) -> str:
        """Deterministic SHA-256 hash ensuring tamper evidence of the consent event."""
        payload = f"{user_id}:{status}:{purpose}:{scope}:{policy_version}:{timestamp_iso}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()
