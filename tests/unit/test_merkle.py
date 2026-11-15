"""
Merkle Transparency Log Unit Tests — Phase 7 (RC1).

Validates RFC 6962 Merkle tree construction, Signed Tree Heads (STH),
cryptographic inclusion proofs, consistency proofs, and tamper detection
per Doc 01 (§10), Doc 02 (FR-08), and Doc 05 (§15).
"""

import tempfile
from app.crypto.canonicalize import canonicalize
from app.crypto.merkle import MerkleTransparencyLog
from app.crypto.signing import key_manager


def test_inclusion_proof_valid() -> None:
    """Valid inclusion proof must verify successfully for all leaves."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MerkleTransparencyLog(log_dir=tmpdir)
        num_leaves = 7

        for i in range(num_leaves):
            tree.append_certificate_event(
                certificate_id=f"cert_inc_{i}",
                event_type="ISSUANCE",
                policy_version="1.0",
                evidence_manifest_digest=f"digest_{i}_{'0' * 32}",
            )

        root_hex = tree.get_root_hash()
        assert len(tree.leaves) == num_leaves

        # Test inclusion proof for each leaf
        for i in range(num_leaves):
            leaf = tree.leaves[i]
            proof = tree.get_inclusion_proof(leaf_index=i, tree_size=num_leaves)
            assert isinstance(proof, list)
            is_valid = MerkleTransparencyLog.verify_inclusion_proof(
                leaf_hash_hex=leaf.leaf_hash,
                leaf_index=i,
                tree_size=num_leaves,
                proof_hex=proof,
                expected_root_hex=root_hex,
            )
            assert is_valid is True, f"Inclusion proof failed for leaf {i}"


def test_inclusion_proof_invalid_on_tamper() -> None:
    """Modified leaf or tampered proof must fail verification."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MerkleTransparencyLog(log_dir=tmpdir)
        for i in range(4):
            tree.append_certificate_event(
                certificate_id=f"cert_tamper_{i}",
                event_type="ISSUANCE",
                policy_version="1.0",
                evidence_manifest_digest=f"hash_{i}",
            )

        root_hex = tree.get_root_hash()
        leaf = tree.leaves[1]
        proof = tree.get_inclusion_proof(leaf_index=1, tree_size=4)

        # 1. Tamper with leaf hash
        tampered_leaf_hash = leaf.leaf_hash[:-4] + "ffff"
        assert (
            MerkleTransparencyLog.verify_inclusion_proof(
                leaf_hash_hex=tampered_leaf_hash,
                leaf_index=1,
                tree_size=4,
                proof_hex=proof,
                expected_root_hex=root_hex,
            )
            is False
        )

        # 2. Tamper with root hash
        tampered_root = root_hex[:-4] + "dead"
        assert (
            MerkleTransparencyLog.verify_inclusion_proof(
                leaf_hash_hex=leaf.leaf_hash,
                leaf_index=1,
                tree_size=4,
                proof_hex=proof,
                expected_root_hex=tampered_root,
            )
            is False
        )


def test_consistency_proof() -> None:
    """Consistency proof between earlier tree snapshot and later tree snapshot must verify."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MerkleTransparencyLog(log_dir=tmpdir)

        # Snapshot 1: 3 leaves
        for i in range(3):
            tree.append_certificate_event(
                certificate_id=f"cert_c_{i}",
                event_type="ISSUANCE",
                policy_version="1.0",
                evidence_manifest_digest=f"digest_c_{i}",
            )
        root_m = tree.get_root_hash()
        size_m = 3

        # Snapshot 2: add 4 more leaves (total 7)
        for i in range(3, 7):
            tree.append_certificate_event(
                certificate_id=f"cert_c_{i}",
                event_type="ISSUANCE",
                policy_version="1.0",
                evidence_manifest_digest=f"digest_c_{i}",
            )
        root_n = tree.get_root_hash()
        size_n = 7

        assert root_m != root_n

        # Generate consistency proof
        proof = tree.get_consistency_proof(m=size_m, n=size_n)
        assert len(proof) > 0

        # Verify consistency
        is_consistent = MerkleTransparencyLog.verify_consistency_proof(
            m=size_m,
            n=size_n,
            root_m_hex=root_m,
            root_n_hex=root_n,
            proof_hex=proof,
        )
        assert is_consistent is True


def test_signed_tree_head_verification() -> None:
    """Signed tree head signature must verify with active Ed25519 verification key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tree = MerkleTransparencyLog(log_dir=tmpdir)
        tree.append_certificate_event(
            certificate_id="cert_sth_01",
            event_type="ISSUANCE",
            policy_version="1.0",
            evidence_manifest_digest="test_digest",
        )

        sth = tree.get_latest_tree_head()
        assert sth.tree_size == 1
        assert len(sth.root_hash) == 64
        assert sth.key_id == key_manager.active_key_id

        # Verify signature over canonical STH payload
        sth_payload = canonicalize({
            "root_hash": sth.root_hash,
            "timestamp": sth.timestamp,
            "tree_size": sth.tree_size,
        })
        is_valid = key_manager.verify(sth_payload, sth.signature)
        assert is_valid is True
