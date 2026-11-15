"""
Verifiable Deletion Certificate ORM Model — Phase 7 (RC1).

Implements cryptographically signed deletion certificate records per Doc 01 (§10) & Doc 02 (FR-08, FR-09).
"""

from datetime import datetime, timezone
import uuid
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Certificate(Base):
    """
    Durable signed deletion certificate backed by Ed25519 digital signature
    and recorded in the append-only Merkle transparency log.
    """
    __tablename__ = "certificates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=lambda: f"cert_{uuid.uuid4().hex[:16]}")
    deletion_request_id: Mapped[str] = mapped_column(String(64), ForeignKey("deletion_requests.id", ondelete="CASCADE"), index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    policy_version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="VALID_COMPLETED", nullable=False)
    issued_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    completion_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    evidence_manifest_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    canonical_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    signature: Mapped[str] = mapped_column(String(128), nullable=False)
    signing_key_id: Mapped[str] = mapped_column(String(50), nullable=False)
    merkle_leaf_index: Mapped[int] = mapped_column(Integer, nullable=False)
    merkle_root_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    verification_url: Mapped[str] = mapped_column(String(255), nullable=False)
    is_revoked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revocation_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    deletion_request = relationship("DeletionRequest")
    user = relationship("User")
