import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(64), primary_key=True, index=True)
    consent_status = Column(Boolean, default=True, nullable=False)
    shard_id = Column(Integer, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    interactions = relationship("UserInteractionRecord", back_populates="user", cascade="all, delete-orphan")
    deletion_requests = relationship("DeletionRequest", back_populates="user", cascade="all, delete-orphan")


class UserInteractionRecord(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    news_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), default_utc_now, nullable=False)
    shard_id = Column(Integer, nullable=False, index=True)
    leaf_hash = Column(String(64), nullable=False, index=True)

    user = relationship("User", back_populates="interactions")


class DeletionRequest(Base):
    __tablename__ = "deletion_requests"

    request_id = Column(String(64), primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False, index=True)
    deletion_type = Column(String(16), nullable=False)  # 'Path A' (pre-training) or 'Path B' (post-training)
    status = Column(String(32), default="pending", nullable=False, index=True)  # pending, tombstoned, retraining, completed
    affected_shards_json = Column(Text, default="[]", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="deletion_requests")
    certificate = relationship("DeletionCertificate", back_populates="request", uselist=False, cascade="all, delete-orphan")

    @property
    def affected_shards(self) -> list:
        return json.loads(self.affected_shards_json or "[]")

    @affected_shards.setter
    def affected_shards(self, shards: list) -> None:
        self.affected_shards_json = json.dumps(shards)


class AuditLogEntry(Base):
    __tablename__ = "audit_log"

    block_id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    action = Column(String(64), nullable=False)
    payload_hash = Column(String(64), nullable=False)
    metrics_json = Column(Text, nullable=True)
    prev_hash = Column(String(64), nullable=False)
    curr_hash = Column(String(64), nullable=False, index=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "block_id": self.block_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "action": self.action,
            "payload_hash": self.payload_hash,
            "metrics": json.loads(self.metrics_json) if self.metrics_json else None,
            "prev_hash": self.prev_hash,
            "curr_hash": self.curr_hash,
        }


class DeletionCertificate(Base):
    __tablename__ = "deletion_certificates"

    certificate_id = Column(String(64), primary_key=True, index=True)
    request_id = Column(String(64), ForeignKey("deletion_requests.request_id"), nullable=False, unique=True)
    user_id = Column(String(64), nullable=False, index=True)
    deletion_type = Column(String(16), nullable=False)
    old_merkle_root = Column(String(64), nullable=False)
    new_merkle_root = Column(String(64), nullable=False)
    merkle_exclusion_proof_json = Column(Text, nullable=False)
    old_model_hash = Column(String(64), nullable=False)
    new_model_hash = Column(String(64), nullable=False)
    ecdsa_signature = Column(Text, nullable=False)
    issuer_public_key_pem = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    request = relationship("DeletionRequest", back_populates="certificate")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "certificate_id": self.certificate_id,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "deletion_type": self.deletion_type,
            "old_merkle_root": self.old_merkle_root,
            "new_merkle_root": self.new_merkle_root,
            "merkle_exclusion_proof": json.loads(self.merkle_exclusion_proof_json or "{}"),
            "old_model_hash": self.old_model_hash,
            "new_model_hash": self.new_model_hash,
            "ecdsa_signature": self.ecdsa_signature,
            "issuer_public_key_pem": self.issuer_public_key_pem,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
