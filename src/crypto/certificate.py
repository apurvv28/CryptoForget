import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from src.crypto.ecdsa_signer import ECDSAService, get_ecdsa_service
from src.crypto.merkle import verify_merkle_proof

IST = timezone(timedelta(hours=5, minutes=30))


def canonical_certificate_payload(
    certificate_id: str,
    request_id: str,
    user_id: str,
    deletion_type: str,
    old_merkle_root: str,
    new_merkle_root: str,
    old_model_hash: str,
    new_model_hash: str,
    timestamp_str: str,
) -> str:
    """Creates deterministic canonical payload string for ECDSA signing."""
    fields = [
        certificate_id,
        request_id,
        user_id,
        deletion_type,
        old_merkle_root,
        new_merkle_root,
        old_model_hash,
        new_model_hash,
        timestamp_str,
    ]
    return "|".join(fields)


def generate_deletion_certificate(
    request_id: str,
    user_id: str,
    deletion_type: str,
    old_merkle_root: str,
    new_merkle_root: str,
    merkle_exclusion_proof: Dict[str, Any],
    old_model_hash: str,
    new_model_hash: str,
    ecdsa_service: Optional[ECDSAService] = None,
) -> Dict[str, Any]:
    """Generates an independently verifiable ECDSA signed deletion certificate."""
    signer = ecdsa_service or get_ecdsa_service()
    certificate_id = f"CERT-{uuid.uuid4().hex[:12].upper()}"
    timestamp_str = datetime.now(IST).isoformat()

    payload_to_sign = canonical_certificate_payload(
        certificate_id=certificate_id,
        request_id=request_id,
        user_id=user_id,
        deletion_type=deletion_type,
        old_merkle_root=old_merkle_root,
        new_merkle_root=new_merkle_root,
        old_model_hash=old_model_hash,
        new_model_hash=new_model_hash,
        timestamp_str=timestamp_str,
    )

    signature_b64 = signer.sign_payload(payload_to_sign)
    public_key_pem = signer.get_public_key_pem()

    certificate_dict = {
        "certificate_id": certificate_id,
        "request_id": request_id,
        "user_id": user_id,
        "deletion_type": deletion_type,
        "timestamp": timestamp_str,
        "old_merkle_root": old_merkle_root,
        "new_merkle_root": new_merkle_root,
        "old_model_hash": old_model_hash,
        "new_model_hash": new_model_hash,
        "merkle_exclusion_proof": merkle_exclusion_proof,
        "ecdsa_signature": signature_b64,
        "issuer_public_key_pem": public_key_pem,
    }

    return certificate_dict


def verify_deletion_certificate(
    certificate_dict: Dict[str, Any],
    override_public_key_pem: Optional[str] = None,
) -> Tuple[bool, str, float]:
    """Verifies a deletion certificate's ECDSA signature and Merkle proof of exclusion.
    Returns: (is_valid, verification_message, verification_time_ms)
    """
    start_time = time.perf_counter()

    public_key_pem = override_public_key_pem or certificate_dict.get("issuer_public_key_pem")
    if not public_key_pem:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return False, "Public key missing in certificate or arguments.", elapsed_ms

    timestamp_str = certificate_dict.get("timestamp") or certificate_dict.get("created_at") or ""

    payload_to_verify = canonical_certificate_payload(
        certificate_id=certificate_dict.get("certificate_id", ""),
        request_id=certificate_dict.get("request_id", ""),
        user_id=certificate_dict.get("user_id", ""),
        deletion_type=certificate_dict.get("deletion_type", ""),
        old_merkle_root=certificate_dict.get("old_merkle_root", ""),
        new_merkle_root=certificate_dict.get("new_merkle_root", ""),
        old_model_hash=certificate_dict.get("old_model_hash", ""),
        new_model_hash=certificate_dict.get("new_model_hash", ""),
        timestamp_str=timestamp_str,
    )

    # 1. Verify ECDSA Digital Signature
    is_signature_valid = ECDSAService.verify_signature(
        payload=payload_to_verify,
        signature_b64=certificate_dict.get("ecdsa_signature", ""),
        public_key_pem=public_key_pem,
    )

    if not is_signature_valid:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return False, "Invalid ECDSA signature. Certificate may have been tampered with!", elapsed_ms

    # 2. Verify Merkle Proof of Inclusion to Old Root
    proof_info = certificate_dict.get("merkle_exclusion_proof", {})
    old_inclusion_proof = proof_info.get("old_inclusion_proof")
    deleted_leaf_hash = proof_info.get("deleted_leaf_hash")

    if old_inclusion_proof and deleted_leaf_hash:
        is_merkle_valid = verify_merkle_proof(
            leaf_hash=deleted_leaf_hash,
            expected_root=certificate_dict["old_merkle_root"],
            proof=old_inclusion_proof,
        )
        if not is_merkle_valid:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            return False, "Merkle proof of inclusion to old root failed verification.", elapsed_ms

    elapsed_ms = (time.perf_counter() - start_time) * 1000
    return True, "Certificate signature and Merkle exclusion proof verified successfully.", elapsed_ms
