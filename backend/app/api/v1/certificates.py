"""Certificate API Endpoints — Phase 7 (RC1)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.certificate import CertificateResponse, RevocationRequest
from app.services.certificate_service import certificate_service

router = APIRouter()


@router.post("/issue/{deletion_request_id}", response_model=CertificateResponse)
async def issue_certificate(
    deletion_request_id: str,
    db: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Issues an Ed25519-signed certificate for a completed deletion request."""
    try:
        return await certificate_service.issue_certificate(
            deletion_request_id=deletion_request_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{certificate_id}", response_model=CertificateResponse)
async def get_certificate(
    certificate_id: str,
    db: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Retrieves an issued certificate for the owner."""
    cert = await certificate_service.get_certificate(certificate_id=certificate_id, db=db)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    return cert


@router.get("/by-request/{deletion_request_id}", response_model=CertificateResponse)
async def get_certificate_by_deletion_request(
    deletion_request_id: str,
    db: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Retrieves the certificate associated with a deletion request."""
    cert = await certificate_service.get_certificate_by_deletion_request(
        deletion_request_id=deletion_request_id,
        db=db,
    )
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found for this deletion request")
    return cert


@router.post("/{certificate_id}/revoke", response_model=CertificateResponse)
async def revoke_certificate(
    certificate_id: str,
    req: RevocationRequest,
    db: AsyncSession = Depends(get_db),
) -> CertificateResponse:
    """Revokes an issued certificate and records a REVOCATION leaf in the Merkle log."""
    try:
        return await certificate_service.revoke_certificate(
            certificate_id=certificate_id,
            reason=req.reason,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
