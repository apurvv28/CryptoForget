"""Data Inventory API Endpoints — Phase 2."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.consent import DataInventoryResponse
from app.services.lineage_service import lineage_service

router = APIRouter()


@router.get("", response_model=DataInventoryResponse)
async def get_data_inventory(db: AsyncSession = Depends(get_db)) -> DataInventoryResponse:
    """Show retained data categories and training eligibility summary per Doc 02 FR-04."""
    return await lineage_service.get_data_inventory(db=db)
