"""Deletion API Endpoints — Phase 5 (RC2) & Phase 6."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.deletion import (
    DeletionCreateRequest,
    DeletionDetailResponse,
    DeletionResponse,
    ExclusionEpochResponse,
)
from app.services.deletion_orchestrator import deletion_orchestrator
from app.services.deletion_service import deletion_service

router = APIRouter()


@router.post("", response_model=DeletionResponse)
async def request_deletion(
    request: DeletionCreateRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> DeletionResponse:
    """
    Submits a deletion request:
    1. Atomically creates tombstones, increments the exclusion epoch, and blocks future processing.
    2. Dispatches asynchronous deletion orchestration (source deletion, unlearning, verification).
    """
    resp = await deletion_service.create_deletion_request(request=request, db=db, user_id=request.user_id)
    if request.auto_orchestrate:
        background_tasks.add_task(deletion_orchestrator.orchestrate_deletion, resp.deletion_request_id)
    return resp


@router.post("/{deletion_id}/orchestrate", response_model=DeletionDetailResponse)
async def trigger_orchestration(
    deletion_id: str,
    synchronous: bool = Query(default=True, description="Wait for orchestration to complete"),
    db: AsyncSession = Depends(get_db),
) -> DeletionDetailResponse:
    """Explicitly triggers or re-runs the deletion orchestration pipeline."""
    if synchronous:
        await deletion_orchestrator.orchestrate_deletion(deletion_id, db=db)
    else:
        import asyncio
        asyncio.create_task(deletion_orchestrator.orchestrate_deletion(deletion_id))

    detail = await deletion_service.get_deletion_detail(deletion_id=deletion_id, db=db)
    if not detail:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    return detail


@router.get("/epoch/current", response_model=ExclusionEpochResponse)
async def get_current_epoch(db: AsyncSession = Depends(get_db)) -> ExclusionEpochResponse:
    """Returns the current dataset exclusion epoch for worker fencing."""
    epoch_obj = await deletion_service.get_or_create_epoch(db)
    return ExclusionEpochResponse(
        scope=epoch_obj.scope,
        epoch=epoch_obj.epoch,
        updated_at=epoch_obj.updated_at,
    )


@router.get("/{deletion_id}", response_model=DeletionDetailResponse)
async def get_deletion_status(
    deletion_id: str,
    db: AsyncSession = Depends(get_db),
) -> DeletionDetailResponse:
    """Inspects comprehensive deletion request status, timeline, store checks, and unlearning metrics."""
    res = await deletion_service.get_deletion_detail(deletion_id=deletion_id, db=db)
    if not res:
        raise HTTPException(status_code=404, detail="Deletion request not found")
    return res
