"""
Merkle Deletion Transparency Log — Phase 7 (RC1).

Implements an append-only RFC 6962-compliant Merkle Tree with domain separation,
cryptographic inclusion proofs, consistency proofs, and Signed Tree Heads (STH)
per Docs 01 (§10, §14), 02 (FR-08, FR-09), and 05 (§15).
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from app.crypto.canonicalize import canonicalize, digest_sha256
from app.crypto.signing import key_manager


LEAF_PREFIX = b"\x00"
NODE_PREFIX = b"\x01"


@dataclass
class LogLeaf:
    """Opaque leaf entry in the deletion transparency log (strictly zero PII)."""
    leaf_index: int
    certificate_id: str
    event_type: str  # "ISSUANCE" | "REVOCATION"
    timestamp: str
    policy_version: str
    evidence_manifest_digest: str
    leaf_hash: str


@dataclass
class SignedTreeHead:
    """Cryptographically signed state of the Merkle log at a specific size."""
    tree_size: int
    root_hash: str
    timestamp: str
    key_id: str
    signature: str


class MerkleTransparencyLog:
    """
    Append-only Merkle tree managing verifiable deletion records.
    RFC 6962 compliant with prefix domain separation:
    - Leaves prefixed with 0x00
    - Internal nodes prefixed with 0x01
    """

    def __init__(self, log_dir: str = "./data/transparency"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.leaves_file = self.log_dir / "leaves.jsonl"
        self.heads_file = self.log_dir / "tree_heads.jsonl"
        self.leaves: list[LogLeaf] = []
        self._load_leaves()

    def _load_leaves(self) -> None:
        """Loads persisted leaves from disk."""
        self.leaves = []
        if self.leaves_file.exists():
            with open(self.leaves_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.leaves.append(LogLeaf(**data))

    def _leaf_hash(self, leaf_data: bytes) -> bytes:
        return hashlib.sha256(LEAF_PREFIX + leaf_data).digest()

    def _node_hash(self, left: bytes, right: bytes) -> bytes:
        return hashlib.sha256(NODE_PREFIX + left + right).digest()

    def _mth(self, leaf_hashes: list[bytes]) -> bytes:
        """Computes Merkle Tree Hash (MTH) recursively per RFC 6962 §2.1."""
        n = len(leaf_hashes)
        if n == 0:
            return hashlib.sha256(b"").digest()
        if n == 1:
            return leaf_hashes[0]

        # Largest power of 2 less than n
        k = 1 << ((n - 1).bit_length() - 1)
        left = self._mth(leaf_hashes[:k])
        right = self._mth(leaf_hashes[k:])
        return self._node_hash(left, right)

    def get_root_hash(self) -> str:
        """Returns the current Merkle tree root hash as a hex string."""
        leaf_hashes = [bytes.fromhex(leaf.leaf_hash) for leaf in self.leaves]
        return self._mth(leaf_hashes).hex()

    def append_certificate_event(
        self,
        certificate_id: str,
        event_type: str,
        policy_version: str,
        evidence_manifest_digest: str,
        timestamp: str | None = None,
    ) -> tuple[LogLeaf, SignedTreeHead]:
        """
        Appends an issuance or revocation leaf to the transparency log.
        Zero PII stored: only opaque certificate ID, event type, and digests.
        """
        leaf_index = len(self.leaves)
        ts = timestamp or datetime.now(timezone.utc).isoformat()

        # Canonicalize payload for leaf hashing
        canonical_leaf_bytes = canonicalize({
            "certificate_id": certificate_id,
            "event_type": event_type,
            "evidence_manifest_digest": evidence_manifest_digest,
            "leaf_index": leaf_index,
            "policy_version": policy_version,
            "timestamp": ts,
        })
        leaf_hash = self._leaf_hash(canonical_leaf_bytes).hex()

        leaf = LogLeaf(
            leaf_index=leaf_index,
            certificate_id=certificate_id,
            event_type=event_type,
            timestamp=ts,
            policy_version=policy_version,
            evidence_manifest_digest=evidence_manifest_digest,
            leaf_hash=leaf_hash,
        )
        self.leaves.append(leaf)

        # Append to leaves file
        with open(self.leaves_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(leaf)) + "\n")

        # Generate new Signed Tree Head (STH)
        sth = self.generate_signed_tree_head()
        return leaf, sth

    def generate_signed_tree_head(self) -> SignedTreeHead:
        """Signs the current root hash and tree size with the active Ed25519 key."""
        tree_size = len(self.leaves)
        root_hash = self.get_root_hash()
        ts = datetime.now(timezone.utc).isoformat()

        sth_payload = canonicalize({
            "root_hash": root_hash,
            "timestamp": ts,
            "tree_size": tree_size,
        })
        sig_b64, key_id = key_manager.sign(sth_payload)

        sth = SignedTreeHead(
            tree_size=tree_size,
            root_hash=root_hash,
            timestamp=ts,
            key_id=key_id,
            signature=sig_b64,
        )

        with open(self.heads_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(sth)) + "\n")

        return sth

    def get_latest_tree_head(self) -> SignedTreeHead:
        """Returns the most recent Signed Tree Head, generating one if none exist."""
        if self.heads_file.exists():
            lines = self.heads_file.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                return SignedTreeHead(**json.loads(lines[-1]))
        return self.generate_signed_tree_head()

    def get_inclusion_proof(self, leaf_index: int, tree_size: int | None = None) -> list[str]:
        """
        Generates an audit inclusion proof for leaf_index in a tree of tree_size per RFC 6962 §2.1.3.
        Returns a list of sibling hashes (in hex).
        """
        if tree_size is None:
            tree_size = len(self.leaves)

        if not (0 <= leaf_index < tree_size <= len(self.leaves)):
            raise IndexError("Invalid leaf index or tree size")

        leaf_hashes = [bytes.fromhex(self.leaves[i].leaf_hash) for i in range(tree_size)]

        def _subproof(m: int, hashes: list[bytes]) -> list[bytes]:
            n = len(hashes)
            if n == 1:
                return []
            k = 1 << ((n - 1).bit_length() - 1)
            if m < k:
                # Target in left subtree, sibling is right subtree MTH
                return _subproof(m, hashes[:k]) + [self._mth(hashes[k:])]
            else:
                # Target in right subtree, sibling is left subtree MTH
                return _subproof(m - k, hashes[k:]) + [self._mth(hashes[:k])]

        proof_bytes = _subproof(leaf_index, leaf_hashes)
        return [b.hex() for b in proof_bytes]

    @classmethod
    def verify_inclusion_proof(
        cls,
        leaf_hash_hex: str,
        leaf_index: int,
        tree_size: int,
        proof_hex: list[str],
        expected_root_hex: str,
    ) -> bool:
        """
        Verifies that leaf_hash_hex is included in the tree of tree_size with expected_root_hex
        per RFC 6962 §2.1.3.
        """
        if not (0 <= leaf_index < tree_size):
            return False

        leaf_bytes = bytes.fromhex(leaf_hash_hex)
        proof_bytes = [bytes.fromhex(p) for p in proof_hex]

        def _verify(target_hash: bytes, m_val: int, n_val: int, proof_list: list[bytes]) -> bytes:
            if n_val == 1:
                return target_hash
            k_val = 1 << ((n_val - 1).bit_length() - 1)
            sibling = proof_list[-1]
            sub = proof_list[:-1]
            if m_val < k_val:
                left = _verify(target_hash, m_val, k_val, sub)
                return hashlib.sha256(NODE_PREFIX + left + sibling).digest()
            else:
                right = _verify(target_hash, m_val - k_val, n_val - k_val, sub)
                return hashlib.sha256(NODE_PREFIX + sibling + right).digest()

        try:
            computed_root = _verify(leaf_bytes, leaf_index, tree_size, proof_bytes)
            return computed_root.hex() == expected_root_hex
        except Exception:
            return False

    def get_consistency_proof(self, m: int, n: int) -> list[str]:
        """
        Generates a consistency proof between tree size m and n (m < n) per RFC 6962 §2.1.2.
        """
        if not (0 < m <= n <= len(self.leaves)):
            raise ValueError("Invalid consistency parameters")

        leaf_hashes = [bytes.fromhex(self.leaves[i].leaf_hash) for i in range(n)]

        def _subconsistency(m_val: int, hashes: list[bytes], b: bool) -> list[bytes]:
            n_val = len(hashes)
            if m_val == n_val:
                return [] if b else [self._mth(hashes)]
            k = 1 << ((n_val - 1).bit_length() - 1)
            if m_val <= k:
                return _subconsistency(m_val, hashes[:k], b) + [self._mth(hashes[k:])]
            else:
                return _subconsistency(m_val - k, hashes[k:], False) + [self._mth(hashes[:k])]

        proof_bytes = _subconsistency(m, leaf_hashes, True)
        return [b.hex() for b in proof_bytes]

    @classmethod
    def verify_consistency_proof(
        cls,
        m: int,
        n: int,
        root_m_hex: str,
        root_n_hex: str,
        proof_hex: list[str],
    ) -> bool:
        """
        Verifies that root_m_hex is an exact prefix of root_n_hex per RFC 6962 §2.1.2.
        """
        if m == n:
            return root_m_hex == root_n_hex and len(proof_hex) == 0
        if not (0 < m < n):
            return False

        proof = [bytes.fromhex(p) for p in proof_hex]
        root_m = bytes.fromhex(root_m_hex)
        root_n = bytes.fromhex(root_n_hex)

        def _sub(m_val: int, n_val: int, proof_list: list[bytes], b: bool) -> tuple[bytes, bytes]:
            if m_val == n_val:
                return (root_m, root_m) if b else (proof_list[0], proof_list[0])
            k = 1 << ((n_val - 1).bit_length() - 1)
            sibling = proof_list[-1]
            subproof = proof_list[:-1]
            if m_val <= k:
                old_sub, new_sub = _sub(m_val, k, subproof, b)
                new_root = hashlib.sha256(NODE_PREFIX + new_sub + sibling).digest()
                return old_sub, new_root
            else:
                old_sub, new_sub = _sub(m_val - k, n_val - k, subproof, False)
                old_root = hashlib.sha256(NODE_PREFIX + sibling + old_sub).digest()
                new_root = hashlib.sha256(NODE_PREFIX + sibling + new_sub).digest()
                return old_root, new_root

        try:
            old_calc, new_calc = _sub(m, n, proof, True)
            return old_calc == root_m and new_calc == root_n
        except Exception:
            return False


# Global singleton
transparency_log = MerkleTransparencyLog()
