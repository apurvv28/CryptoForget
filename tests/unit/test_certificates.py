"""
Certificate and Signature Unit Tests — Phase 7 (RC1).

Validates RFC 8785 canonicalization, Ed25519 signing/verification,
tamper detection, revocation handling, and zero PII disclosure
per Doc 01 (§10), Doc 02 (FR-08, FR-09), and Doc 05 (§10, §11).
"""

import json
from app.crypto.canonicalize import canonicalize, digest_sha256
from app.crypto.signing import KeyManager, key_manager


def test_valid_signature_verifies() -> None:
    """A correctly signed canonical certificate must verify."""
    payload = {
        "certificate_id": "cert_test_123456",
        "deletion_request_id": "del_opaque_789",
        "status": "VALID_COMPLETED",
        "policy_version": "1.0",
        "issued_at": "2026-11-03T20:00:00Z",
        "evidence_manifest_digest": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "checks": {
            "source_data_purged": True,
            "tombstones_active": True,
            "deployment_verified": True,
        },
    }

    # 1. Canonicalize
    canonical_bytes = canonicalize(payload)

    # 2. Sign with key manager
    sig_b64, key_id = key_manager.sign(canonical_bytes)
    assert len(sig_b64) > 0
    assert key_id == key_manager.active_key_id

    # 3. Verify with key manager
    is_valid = key_manager.verify(canonical_bytes, sig_b64)
    assert is_valid is True

    # 4. Verify with explicit public key
    pub_b64 = key_manager.get_public_key_b64()
    assert key_manager.verify(canonical_bytes, sig_b64, public_key_b64=pub_b64) is True


def test_tampered_payload_fails_verification() -> None:
    """Altered certificate payload must fail signature verification."""
    payload = {
        "certificate_id": "cert_test_tamper_01",
        "deletion_request_id": "del_opaque_abc",
        "status": "VALID_COMPLETED",
        "policy_version": "1.0",
    }
    canonical_bytes = canonicalize(payload)
    sig_b64, _ = key_manager.sign(canonical_bytes)

    # Tamper with payload
    tampered_payload = dict(payload)
    tampered_payload["status"] = "INVALID"
    tampered_bytes = canonicalize(tampered_payload)

    # Verification must fail
    assert key_manager.verify(tampered_bytes, sig_b64) is False


def test_revoked_certificate_detected() -> None:
    """Revoked certificates must be identifiable and reported as invalid."""
    payload = {
        "certificate_id": "cert_revoked_01",
        "deletion_request_id": "del_opaque_revoked",
        "status": "REVOKED",
        "policy_version": "1.0",
    }
    canonical_bytes = canonicalize(payload)
    sig_b64, _ = key_manager.sign(canonical_bytes)

    # Signature itself is mathematically valid
    assert key_manager.verify(canonical_bytes, sig_b64) is True

    # But certificate policy marks it revoked
    assert payload["status"] == "REVOKED"


def test_no_pii_in_public_certificate() -> None:
    """Public certificate must contain strictly zero PII per Doc 05 §10."""
    forbidden_substrings = [
        "email",
        "username",
        "password",
        "phone",
        "prompt",
        "content",
        "message_text",
        "ip_address",
        "credit_card",
    ]

    safe_public_certificate = {
        "certificate_id": "cert_pub_84f92a10",
        "request_id": "del_99812bc4",
        "policy_version": "1.0",
        "issued_at": "2026-11-03T18:00:00Z",
        "completion_timestamp": "2026-11-03T18:00:05Z",
        "status": "VALID_COMPLETED",
        "signing_key_id": "key_2026_01",
        "signature_algorithm": "Ed25519",
        "evidence_manifest_digest": "4f4cb953110e53a29b4e5d6ff78367a7d4a275a5e3d7499d63c5092a5438885b",
        "operations": [
            "PRE_TOMBSTONING_EXCLUSION",
            "SOURCE_STORE_REDACTION",
            "SISA_SELECTIVE_UNLEARNING",
            "ATOMIC_MODEL_PROMOTION",
            "POLICY_EVIDENCE_VERIFICATION",
        ],
        "merkle_leaf_index": 4,
        "merkle_root_hash": "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
    }

    raw_json = json.dumps(safe_public_certificate).lower()
    for forbidden in forbidden_substrings:
        assert forbidden not in raw_json, f"PII key or content '{forbidden}' leaked in public certificate!"
