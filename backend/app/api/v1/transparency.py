"""Merkle Transparency Log API Endpoints — Phase 7 (RC1)."""

from fastapi import APIRouter, HTTPException, Query
from app.crypto.merkle import transparency_log
from app.schemas.certificate import MerkleInclusionProofResponse, SignedTreeHeadResponse

router = APIRouter()


@router.get("/tree-head", response_model=SignedTreeHeadResponse)
async def get_latest_tree_head() -> SignedTreeHeadResponse:
    """Returns the latest cryptographically signed tree head (STH)."""
    sth = transparency_log.get_latest_tree_head()
    return SignedTreeHeadResponse(
        tree_size=sth.tree_size,
        root_hash=sth.root_hash,
        timestamp=sth.timestamp,
        key_id=sth.key_id,
        signature=sth.signature,
    )


@router.get("/leaves/{leaf_index}")
async def get_log_leaf(leaf_index: int):
    """Returns an opaque log leaf (strictly zero PII)."""
    if not (0 <= leaf_index < len(transparency_log.leaves)):
        raise HTTPException(status_code=404, detail="Leaf index out of range")
    leaf = transparency_log.leaves[leaf_index]
    return {
        "leaf_index": leaf.leaf_index,
        "certificate_id": leaf.certificate_id,
        "event_type": leaf.event_type,
        "timestamp": leaf.timestamp,
        "policy_version": leaf.policy_version,
        "evidence_manifest_digest": leaf.evidence_manifest_digest,
        "leaf_hash": leaf.leaf_hash,
    }


@router.get("/proof/inclusion/{leaf_index}", response_model=MerkleInclusionProofResponse)
async def get_inclusion_proof(
    leaf_index: int,
    tree_size: int | None = Query(default=None, description="Optional tree size snapshot"),
) -> MerkleInclusionProofResponse:
    """Returns an RFC 6962 inclusion proof for a leaf in the transparency log."""
    actual_size = tree_size if tree_size is not None else len(transparency_log.leaves)
    if not (0 <= leaf_index < actual_size <= len(transparency_log.leaves)):
        raise HTTPException(status_code=400, detail="Invalid leaf index or tree size")

    proof = transparency_log.get_inclusion_proof(leaf_index=leaf_index, tree_size=actual_size)
    leaf = transparency_log.leaves[leaf_index]
    root_hash = transparency_log.get_root_hash() if tree_size is None else transparency_log.get_latest_tree_head().root_hash

    is_valid = transparency_log.verify_inclusion_proof(
        leaf_hash_hex=leaf.leaf_hash,
        leaf_index=leaf_index,
        tree_size=actual_size,
        proof_hex=proof,
        expected_root_hex=root_hash,
    )

    return MerkleInclusionProofResponse(
        leaf_index=leaf_index,
        tree_size=actual_size,
        leaf_hash=leaf.leaf_hash,
        root_hash=root_hash,
        proof=proof,
        verified=is_valid,
    )


@router.get("/proof/consistency")
async def get_consistency_proof(
    m: int = Query(..., description="Earlier tree size"),
    n: int = Query(..., description="Later tree size"),
):
    """Returns an RFC 6962 consistency proof between tree size m and n."""
    try:
        proof = transparency_log.get_consistency_proof(m=m, n=n)
        return {
            "m": m,
            "n": n,
            "proof": proof,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
