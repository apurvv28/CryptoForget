import hashlib
from typing import Any, Dict, List, Optional, Tuple


def sha256_hash(data: str) -> str:
    """Standard SHA-256 hash helper."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def compute_leaf_hash(payload: str) -> str:
    """Computes SHA-256 leaf hash with domain separation prefix (0x00) to prevent 2nd-preimage attacks."""
    return hashlib.sha256(f"\x00{payload}".encode("utf-8")).hexdigest()


def compute_parent_hash(left_hash: str, right_hash: str) -> str:
    """Computes parent node hash from left and right children with domain separation prefix (0x01)."""
    return hashlib.sha256(f"\x01{left_hash}{right_hash}".encode("utf-8")).hexdigest()


class MerkleTree:
    """SHA-256 Merkle Tree implementation providing Proof of Inclusion & Proof of Exclusion."""

    def __init__(self, leaves: Optional[List[str]] = None) -> None:
        self.leaves: List[str] = leaves or []
        self.leaf_hashes: List[str] = [compute_leaf_hash(leaf) for leaf in self.leaves] if leaves else []
        self.levels: List[List[str]] = []
        if self.leaf_hashes:
            self._build_tree()

    @classmethod
    def from_hashes(cls, leaf_hashes: List[str]) -> "MerkleTree":
        """Instantiates Merkle Tree directly from pre-computed leaf hashes."""
        tree = cls()
        tree.leaf_hashes = list(leaf_hashes)
        if tree.leaf_hashes:
            tree._build_tree()
        return tree

    def _build_tree(self) -> None:
        """Constructs binary Merkle tree levels bottom-up."""
        if not self.leaf_hashes:
            self.levels = [[]]
            return

        current_level = list(self.leaf_hashes)
        self.levels = [current_level]

        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = compute_parent_hash(left, right)
                next_level.append(parent)
            self.levels.append(next_level)
            current_level = next_level

    def get_root(self) -> str:
        """Returns the Merkle root hash (or empty string if tree is empty)."""
        if not self.levels or not self.levels[-1]:
            return ""
        return self.levels[-1][0]

    def get_inclusion_proof(self, leaf_hash: str) -> List[Dict[str, str]]:
        """Generates Merkle Proof of Inclusion for a leaf hash.
        Returns list of dicts: [{'position': 'left'|'right', 'hash': str}, ...]
        """
        if leaf_hash not in self.leaf_hashes:
            raise ValueError(f"Leaf hash {leaf_hash} not found in Merkle Tree.")

        index = self.leaf_hashes.index(leaf_hash)
        proof = []

        for level in self.levels[:-1]:
            is_right_child = (index % 2 == 1)
            sibling_index = index - 1 if is_right_child else index + 1

            if sibling_index < len(level):
                sibling_hash = level[sibling_index]
            else:
                sibling_hash = level[index]  # Duplicate odd node

            proof.append({
                "position": "left" if is_right_child else "right",
                "hash": sibling_hash
            })
            index = index // 2

        return proof

    def get_exclusion_proof(self, deleted_leaf_hash: str, new_tree: "MerkleTree") -> Dict[str, Any]:
        """Generates Proof of Exclusion showing that `deleted_leaf_hash` existed in the old tree
        (with inclusion proof to old root) and is verifiably ABSENT in the new tree."""
        if deleted_leaf_hash not in self.leaf_hashes:
            raise ValueError(f"Leaf hash {deleted_leaf_hash} not in original Merkle Tree.")

        if deleted_leaf_hash in new_tree.leaf_hashes:
            raise ValueError(f"Leaf hash {deleted_leaf_hash} is still present in the new Merkle Tree!")

        inclusion_proof_old = self.get_inclusion_proof(deleted_leaf_hash)

        return {
            "deleted_leaf_hash": deleted_leaf_hash,
            "old_root": self.get_root(),
            "new_root": new_tree.get_root(),
            "old_inclusion_proof": inclusion_proof_old,
            "is_absent_in_new_root": True,
            "new_tree_leaf_count": len(new_tree.leaf_hashes)
        }


def verify_merkle_proof(leaf_hash: str, expected_root: str, proof: List[Dict[str, str]]) -> bool:
    """Verifies a Merkle inclusion proof against an expected root hash."""
    current_hash = leaf_hash
    for step in proof:
        sibling_hash = step["hash"]
        position = step["position"]

        if position == "left":
            current_hash = compute_parent_hash(sibling_hash, current_hash)
        else:
            current_hash = compute_parent_hash(current_hash, sibling_hash)

    return current_hash == expected_root
