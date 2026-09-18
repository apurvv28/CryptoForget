from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from src.agents.user_simulator import get_agent_manager
from src.crypto.certificate import verify_deletion_certificate
from src.db.database import get_db
from src.db.models import DeletionCertificate, DeletionRequest
from src.unlearning.unlearner import UnlearningEngine

router = APIRouter(prefix="/api/v1", tags=["Machine Unlearning & Certificates"])

# Shared engine instance
engine_instance = UnlearningEngine()


class DeleteUserRequest(BaseModel):
    user_id: str = Field(..., description="Target User ID to unlearn/delete")
    deletion_type: str = Field(default="Path B", description="Path A (pre-training tombstoning) or Path B (SISA shard retraining)")


class VerifyCertificateRequest(BaseModel):
    certificate: Dict[str, Any] = Field(..., description="Full Deletion Certificate JSON object")
    public_key_pem: Optional[str] = Field(None, description="Optional override public key PEM string")


@router.post("/delete-user", response_model=Dict[str, Any])
def request_user_deletion(
    req: DeleteUserRequest,
    db: Session = Depends(get_db),
):
    """Submits a right-to-be-forgotten unlearning request.
    Executes Path A tombstoning or Path B SISA shard retraining, issues an ECDSA signed deletion certificate,
    and records the event in the append-only audit log.
    """
    if req.deletion_type not in ["Path A", "Path B"]:
        raise HTTPException(status_code=400, detail="Invalid deletion_type. Must be 'Path A' or 'Path B'.")

    try:
        cert_dict = engine_instance.execute_unlearning(
            session=db,
            user_id=req.user_id,
            request_type=req.deletion_type,
        )

        # Update simulated agent status
        agent_mgr = get_agent_manager()
        agent_mgr.mark_unlearned(req.user_id)

        return {
            "status": "COMPLETED",
            "message": f"Successfully unlearned user {req.user_id} via {req.deletion_type}.",
            "certificate": cert_dict,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/unlearning-status/{request_id}", response_model=Dict[str, Any])
def get_unlearning_status(
    request_id: str,
    db: Session = Depends(get_db),
):
    """Queries the status of an unlearning request by request_id."""
    del_req = db.query(DeletionRequest).filter(DeletionRequest.request_id == request_id).first()
    if not del_req:
        raise HTTPException(status_code=404, detail=f"Unlearning request {request_id} not found.")

    return {
        "request_id": del_req.request_id,
        "user_id": del_req.user_id,
        "deletion_type": del_req.deletion_type,
        "status": del_req.status,
        "affected_shards": del_req.affected_shards,
        "created_at": del_req.created_at.isoformat() if del_req.created_at else None,
        "completed_at": del_req.completed_at.isoformat() if del_req.completed_at else None,
    }


@router.get("/certificate/{user_id}", response_model=Dict[str, Any])
def get_user_certificate(
    user_id: str,
    db: Session = Depends(get_db),
):
    """Retrieves the latest signed deletion certificate issued for a user."""
    cert = (
        db.query(DeletionCertificate)
        .filter(DeletionCertificate.user_id == user_id)
        .order_by(DeletionCertificate.created_at.desc())
        .first()
    )
    if not cert:
        raise HTTPException(status_code=404, detail=f"No deletion certificate found for user {user_id}.")

    return cert.to_dict()


@router.post("/verify-certificate", response_model=Dict[str, Any])
def verify_certificate(req: VerifyCertificateRequest):
    """Independently verifies an ECDSA signed deletion certificate and Merkle exclusion proof."""
    is_valid, message, latency_ms = verify_deletion_certificate(
        certificate_dict=req.certificate,
        override_public_key_pem=req.public_key_pem,
    )

    return {
        "is_valid": is_valid,
        "message": message,
        "verification_time_ms": round(latency_ms, 3),
        "target_max_latency_ms": 100.0,
    }
