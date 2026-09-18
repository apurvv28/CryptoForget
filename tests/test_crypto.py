import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.crypto.audit_log import AuditLedger
from src.crypto.certificate import generate_deletion_certificate, verify_deletion_certificate
from src.crypto.ecdsa_signer import ECDSAService
from src.crypto.merkle import MerkleTree, compute_leaf_hash, verify_merkle_proof
from src.db.database import drop_db, get_db_session, init_db


def test_merkle_tree_inclusion_proof():
    users = ["U1000:N1 N2 N3", "U1001:N4 N5", "U1002:N6 N7 N8", "U1003:N9"]
    tree = MerkleTree(users)
    root = tree.get_root()
    assert root != ""

    target_leaf_hash = compute_leaf_hash(users[1])
    proof = tree.get_inclusion_proof(target_leaf_hash)

    assert len(proof) > 0
    assert verify_merkle_proof(target_leaf_hash, root, proof) is True


def test_merkle_exclusion_proof():
    original_users = ["U1000:N1 N2", "U1001:N3 N4", "U1002:N5 N6"]
    old_tree = MerkleTree(original_users)

    # Simulate deletion of U1001
    remaining_users = ["U1000:N1 N2", "U1002:N5 N6"]
    new_tree = MerkleTree(remaining_users)

    deleted_leaf_hash = compute_leaf_hash("U1001:N3 N4")
    exclusion_proof = old_tree.get_exclusion_proof(deleted_leaf_hash, new_tree)

    assert exclusion_proof["deleted_leaf_hash"] == deleted_leaf_hash
    assert exclusion_proof["old_root"] == old_tree.get_root()
    assert exclusion_proof["new_root"] == new_tree.get_root()
    assert exclusion_proof["is_absent_in_new_root"] is True


def test_ecdsa_signing_and_verification():
    ecdsa_svc = ECDSAService()
    payload = "Sample deletion event payload: U1000 deleted at 2026-09-18"
    signature = ecdsa_svc.sign_payload(payload)
    pub_key_pem = ecdsa_svc.get_public_key_pem()

    assert signature != ""
    assert ecdsa_svc.verify_signature(payload, signature, pub_key_pem) is True

    # Modified payload should fail verification
    assert ecdsa_svc.verify_signature(payload + "tampered", signature, pub_key_pem) is False


def test_audit_ledger_integrity():
    drop_db()
    init_db()
    with get_db_session() as session:
        ledger = AuditLedger(session)

        # Append two blocks
        b1 = ledger.append_block("USER_INGESTION", "User U1000 ingested")
        b2 = ledger.append_block("USER_UNLEARN_REQUEST", "User U1000 unlearned")

        is_valid, err = ledger.verify_ledger_integrity()
        assert is_valid is True, f"Integrity error: {err}"


def test_deletion_certificate_generation_and_latency():
    old_users = ["U1000:N1 N2", "U1001:N3 N4"]
    old_tree = MerkleTree(old_users)
    new_tree = MerkleTree(["U1000:N1 N2"])

    deleted_hash = compute_leaf_hash("U1001:N3 N4")
    exclusion_proof = old_tree.get_exclusion_proof(deleted_hash, new_tree)

    cert = generate_deletion_certificate(
        request_id="REQ-12345",
        user_id="U1001",
        deletion_type="Path B",
        old_merkle_root=old_tree.get_root(),
        new_merkle_root=new_tree.get_root(),
        merkle_exclusion_proof=exclusion_proof,
        old_model_hash="HASH_OLD_MODEL_123",
        new_model_hash="HASH_NEW_MODEL_456",
    )

    is_valid, msg, latency_ms = verify_deletion_certificate(cert)

    assert is_valid is True
    assert "verified successfully" in msg
    assert latency_ms < 100.0  # Verification latency MUST be under 100 ms as per Benchmarking Matrix
