"""Consent API Endpoints — Phase 2."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.consent import ConsentStatusResponse, ConsentUpdateRequest
from app.services.consent_service import consent_service

router = APIRouter()


@router.get("", response_model=ConsentStatusResponse)
async def get_consent(db: AsyncSession = Depends(get_db)) -> ConsentStatusResponse:
    """Retrieve current effective training consent and versioned event history."""
    return await consent_service.get_current_consent(db=db)


@router.put("", response_model=ConsentStatusResponse)
async def update_consent(
    request: ConsentUpdateRequest,
    db: AsyncSession = Depends(get_db),
) -> ConsentStatusResponse:
    """Grant or withdraw training consent, recording an immutable audit event."""
    return await consent_service.update_consent(request=request, db=db)
