"""
Certificate and Verification Schemas — Phase 7 (RC1).

Defines privacy-preserving schema contracts for owner certificates,
public verification pages, and Merkle transparency proofs per Doc 01 (§10) & Doc 05 (§10).
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class CertificateResponse(BaseModel):
    """Authenticated owner view of a verifiable deletion certificate."""
    certificate_id: str
    deletion_request_id: str
    policy_version: str
    status: str
    issued_at: datetime
    completion_timestamp: datetime
    evidence_manifest_digest: str
    signature: str
    signing_key_id: str
    signature_algorithm: str = "Ed25519"
    merkle_leaf_index: int
    merkle_root_hash: str
    verification_url: str
    is_revoked: bool = False
    operations: list[str] = Field(default_factory=list)
    checks: dict[str, Any] = Field(default_factory=dict)
    policy_notice: str

    model_config = {"from_attributes": True}


class PublicVerificationResponse(BaseModel):
    """
    Public verification outcome for third-party auditors per Doc 05 §10.
    Strictly zero PII, zero account IDs, zero message texts.
    """
    certificate_id: str
    request_id: str
    verification_status: str  # "VALID_COMPLETED" | "VALID_PENDING" | "INVALID"
    signature_valid: bool
    merkle_inclusion_valid: bool
    issued_at: str
    completion_timestamp: str
    policy_version: str
    signing_key_id: str
    signature_algorithm: str = "Ed25519"
    evidence_manifest_digest: str
    merkle_root_hash: str
    merkle_leaf_index: int
    operations: list[str] = Field(default_factory=list)
    policy_checks: dict[str, bool] = Field(default_factory=dict)
    trust_notice: str


class MerkleInclusionProofResponse(BaseModel):
    """Cryptographic audit path verifying a certificate's inclusion in the transparency log."""
    leaf_index: int
    tree_size: int
    leaf_hash: str
    root_hash: str
    proof: list[str]
    verified: bool


class SignedTreeHeadResponse(BaseModel):
    """Cryptographically signed state of the Merkle transparency log."""
    tree_size: int
    root_hash: str
    timestamp: str
    key_id: str
    signature: str


class RevocationRequest(BaseModel):
    """Request to revoke an issued certificate."""
    reason: str = Field(default="Administrative revocation / policy reassessment")
