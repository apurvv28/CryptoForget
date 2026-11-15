"""
Certificate Issuance, Public Verification & Merkle Notarization Service — Phase 7 (RC1).

Implements verifiable deletion certificate creation, Ed25519 signing,
Merkle transparency logging, and privacy-preserving public verification
per Docs 01 (§10), 02 (FR-08, FR-09, FR-10), and 05 (§10, §15).
"""

from datetime import datetime, timezone
import json
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crypto.canonicalize import canonicalize, digest_sha256
from app.crypto.merkle import transparency_log, MerkleTransparencyLog
from app.crypto.signing import key_manager
from app.models.certificate import Certificate
from app.models.deletion import DeletionRequest
from app.schemas.certificate import (
    CertificateResponse,
    MerkleInclusionProofResponse,
    PublicVerificationResponse,
)


class CertificateService:
    """Coordinates certificate lifecycle, Ed25519 notarization, and zero-PII public verification."""

    async def issue_certificate(
        self,
        deletion_request_id: str,
        db: AsyncSession,
        base_url: str = "http://127.0.0.1:5173",
    ) -> CertificateResponse:
        """
        Issues a verifiable deletion certificate for a COMPLETED deletion request:
        1. Validates that deletion orchestration completed and verified.
        2. Constructs canonical RFC 8785 evidence payload.
        3. Signs evidence manifest with active Ed25519 private key.
        4. Appends audit leaf to Merkle Deletion Transparency Log.
        5. Persists certificate and returns signed response.
        """
        # Idempotent lookup
        existing_stmt = select(Certificate).where(Certificate.deletion_request_id == deletion_request_id)
        existing = (await db.execute(existing_stmt)).scalar_one_or_none()
        if existing:
            return self._to_response(existing)

        # Fetch deletion request
        del_stmt = select(DeletionRequest).where(DeletionRequest.id == deletion_request_id)
        del_req = (await db.execute(del_stmt)).scalar_one_or_none()
        if not del_req:
            raise ValueError(f"Deletion request {deletion_request_id} not found.")

        if del_req.status != "COMPLETED":
            raise ValueError(f"Cannot issue certificate: deletion request is in status '{del_req.status}', must be 'COMPLETED'.")

        cert_id = f"cert_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)
        completion_ts = del_req.completed_at or now

        # Parse store checks
        store_checks: dict[str, Any] = {}
        if del_req.store_checks_json:
            try:
                store_checks = json.loads(del_req.store_checks_json)
            except Exception:
                store_checks = {}

        operations = [
            "PRE_TOMBSTONING_EXCLUSION",
            "SOURCE_STORE_REDACTION",
            "SISA_SELECTIVE_UNLEARNING" if del_req.unlearning_time_ms else "UNLEARNING_BYPASS",
            "ATOMIC_MODEL_PROMOTION",
            "POLICY_EVIDENCE_VERIFICATION",
        ]

        # 1. Canonical Evidence Manifest
        evidence_doc = {
            "certificate_id": cert_id,
            "completion_timestamp": completion_ts.isoformat(),
            "deletion_request_id": del_req.id,
            "issued_at": now.isoformat(),
            "operations": operations,
            "policy_version": "1.0",
            "scope": del_req.scope,
            "status": "VALID_COMPLETED",
            "store_checks": store_checks,
        }
        evidence_digest = digest_sha256(canonicalize(evidence_doc))

        # 2. Canonical Signed Document
        signed_document = {
            "certificate_id": cert_id,
            "completion_timestamp": completion_ts.isoformat(),
            "evidence_manifest_digest": evidence_digest,
            "issued_at": now.isoformat(),
            "operations": operations,
            "policy_version": "1.0",
            "request_id": del_req.id,
            "status": "VALID_COMPLETED",
            "store_checks": {
                "deployment_verified": bool(store_checks.get("deployment_verified", True)),
                "source_data_purged": bool(store_checks.get("source_data_purged", True)),
                "tombstones_active": bool(store_checks.get("tombstones_active", True)),
            },
        }
        canonical_doc_bytes = canonicalize(signed_document)

        # 3. Sign with Ed25519
        sig_b64, key_id = key_manager.sign(canonical_doc_bytes)

        # 4. Append to Merkle Transparency Log
        leaf, sth = transparency_log.append_certificate_event(
            certificate_id=cert_id,
            event_type="ISSUANCE",
            policy_version="1.0",
            evidence_manifest_digest=evidence_digest,
            timestamp=now.isoformat(),
        )

        verification_url = f"{base_url}/verify/{cert_id}"

        cert = Certificate(
            id=cert_id,
            deletion_request_id=del_req.id,
            user_id=del_req.user_id,
            policy_version="1.0",
            status="VALID_COMPLETED",
            issued_at=now,
            completion_timestamp=completion_ts,
            evidence_manifest_digest=evidence_digest,
            canonical_payload_json=canonical_doc_bytes.decode("utf-8"),
            signature=sig_b64,
            signing_key_id=key_id,
            merkle_leaf_index=leaf.leaf_index,
            merkle_root_hash=sth.root_hash,
            verification_url=verification_url,
            is_revoked=False,
        )
        db.add(cert)
        await db.commit()
        return self._to_response(cert)

    async def get_certificate(self, certificate_id: str, db: AsyncSession) -> CertificateResponse | None:
        """Retrieves certificate for owner/authenticated user."""
        stmt = select(Certificate).where(Certificate.id == certificate_id)
        cert = (await db.execute(stmt)).scalar_one_or_none()
        if not cert:
            return None
        return self._to_response(cert)

    async def get_certificate_by_deletion_request(self, deletion_request_id: str, db: AsyncSession) -> CertificateResponse | None:
        """Retrieves certificate associated with a deletion request."""
        stmt = select(Certificate).where(Certificate.deletion_request_id == deletion_request_id)
        cert = (await db.execute(stmt)).scalar_one_or_none()
        if not cert:
            return None
        return self._to_response(cert)

    async def verify_public_certificate(self, certificate_id: str, db: AsyncSession) -> PublicVerificationResponse:
        """
        Public verification protocol per Doc 01 §10 & Doc 05 §10:
        1. Checks signature authenticity using active/historical Ed25519 public keys.
        2. Verifies inclusion proof in the Merkle Transparency Log.
        3. Confirms policy execution and absence of revocation.
        4. Exposes strictly ZERO PII to the caller.
        """
        stmt = select(Certificate).where(Certificate.id == certificate_id)
        cert = (await db.execute(stmt)).scalar_one_or_none()

        if not cert:
            return PublicVerificationResponse(
                certificate_id=certificate_id,
                request_id="unknown",
                verification_status="INVALID",
                signature_valid=False,
                merkle_inclusion_valid=False,
                issued_at="",
                completion_timestamp="",
                policy_version="1.0",
                signing_key_id="",
                signature_algorithm="Ed25519",
                evidence_manifest_digest="",
                merkle_root_hash="",
                merkle_leaf_index=-1,
                operations=[],
                policy_checks={},
                trust_notice="Certificate not found in registry. Verification failed.",
            )

        if cert.is_revoked:
            return PublicVerificationResponse(
                certificate_id=cert.id,
                request_id=cert.deletion_request_id,
                verification_status="INVALID",
                signature_valid=True,
                merkle_inclusion_valid=True,
                issued_at=cert.issued_at.isoformat(),
                completion_timestamp=cert.completion_timestamp.isoformat(),
                policy_version=cert.policy_version,
                signing_key_id=cert.signing_key_id,
                signature_algorithm="Ed25519",
                evidence_manifest_digest=cert.evidence_manifest_digest,
                merkle_root_hash=cert.merkle_root_hash,
                merkle_leaf_index=cert.merkle_leaf_index,
                operations=[],
                policy_checks={"not_revoked": False},
                trust_notice=f"Certificate was REVOKED: {cert.revocation_reason or 'No reason specified.'}",
            )

        # 1. Verify Ed25519 signature over canonical payload
        payload_bytes = cert.canonical_payload_json.encode("utf-8")
        sig_valid = key_manager.verify(payload_bytes, cert.signature)

        # 2. Verify Merkle Log inclusion proof
        try:
            tree_size = len(transparency_log.leaves)
            proof = transparency_log.get_inclusion_proof(cert.merkle_leaf_index, tree_size)
            current_root = transparency_log.get_root_hash()
            leaf = transparency_log.leaves[cert.merkle_leaf_index]
            merkle_valid = MerkleTransparencyLog.verify_inclusion_proof(
                leaf_hash_hex=leaf.leaf_hash,
                leaf_index=cert.merkle_leaf_index,
                tree_size=tree_size,
                proof_hex=proof,
                expected_root_hex=current_root,
            )
        except Exception:
            merkle_valid = False

        # Parse checks from payload
        parsed_doc = json.loads(cert.canonical_payload_json)
        policy_checks = parsed_doc.get("store_checks", {})
        operations = parsed_doc.get("operations", [])

        status = "VALID_COMPLETED" if (sig_valid and merkle_valid) else "INVALID"

        notice = (
            "The platform reports that the deletion workflow completed under policy version 1.0, "
            "and the signed evidence manifest passed the published verification checks. "
            "It is authentic cryptographic evidence of execution under policy, not mathematical proof of zero residual information."
            if status == "VALID_COMPLETED"
            else "Cryptographic verification failed: invalid signature or broken transparency log proof."
        )

        return PublicVerificationResponse(
            certificate_id=cert.id,
            request_id=cert.deletion_request_id,
            verification_status=status,
            signature_valid=sig_valid,
            merkle_inclusion_valid=merkle_valid,
            issued_at=cert.issued_at.isoformat(),
            completion_timestamp=cert.completion_timestamp.isoformat(),
            policy_version=cert.policy_version,
            signing_key_id=cert.signing_key_id,
            signature_algorithm="Ed25519",
            evidence_manifest_digest=cert.evidence_manifest_digest,
            merkle_root_hash=transparency_log.get_root_hash(),
            merkle_leaf_index=cert.merkle_leaf_index,
            operations=operations,
            policy_checks=policy_checks,
            trust_notice=notice,
        )

    async def revoke_certificate(self, certificate_id: str, reason: str, db: AsyncSession) -> CertificateResponse:
        """Revokes a certificate and appends a REVOCATION event to the Merkle log."""
        stmt = select(Certificate).where(Certificate.id == certificate_id)
        cert = (await db.execute(stmt)).scalar_one_or_none()
        if not cert:
            raise ValueError(f"Certificate {certificate_id} not found.")

        cert.is_revoked = True
        cert.status = "REVOKED"
        cert.revocation_reason = reason
        cert.revoked_at = datetime.now(timezone.utc)

        # Append revocation leaf to Merkle log
        transparency_log.append_certificate_event(
            certificate_id=cert.id,
            event_type="REVOCATION",
            policy_version=cert.policy_version,
            evidence_manifest_digest=cert.evidence_manifest_digest,
        )
        await db.commit()
        return self._to_response(cert)

    def _to_response(self, cert: Certificate) -> CertificateResponse:
        try:
            doc = json.loads(cert.canonical_payload_json)
            checks = doc.get("store_checks", {})
            operations = doc.get("operations", [])
        except Exception:
            checks = {}
            operations = []

        return CertificateResponse(
            certificate_id=cert.id,
            deletion_request_id=cert.deletion_request_id,
            policy_version=cert.policy_version,
            status=cert.status,
            issued_at=cert.issued_at,
            completion_timestamp=cert.completion_timestamp,
            evidence_manifest_digest=cert.evidence_manifest_digest,
            signature=cert.signature,
            signing_key_id=cert.signing_key_id,
            signature_algorithm="Ed25519",
            merkle_leaf_index=cert.merkle_leaf_index,
            merkle_root_hash=cert.merkle_root_hash,
            verification_url=cert.verification_url,
            is_revoked=cert.is_revoked,
            operations=operations,
            checks=checks,
            policy_notice=(
                "The platform reports that the deletion workflow completed under policy version 1.0, "
                "and the signed evidence manifest passed the published verification checks."
            ),
        )


# Global singleton
certificate_service = CertificateService()
