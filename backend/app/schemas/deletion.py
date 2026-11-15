"""Deletion Request, Detail, and Epoch Schemas — Phase 5 (RC2) & Phase 6."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class DeletionCreateRequest(BaseModel):
    """User request to initiate deletion and SISA unlearning."""
    scope: str = Field(default="all_user_data", description="Scope of deletion")
    user_id: int | None = Field(default=None, description="Target user ID (admin or auth user)")
    conversation_ids: list[int] | None = Field(default=None, description="Optional conversation IDs")
    idempotency_key: str | None = Field(default=None, description="Client idempotency key")
    auto_orchestrate: bool = Field(default=True, description="Whether to immediately trigger the deletion orchestrator")


class TimelineEvent(BaseModel):
    """Event in the deletion lifecycle timeline."""
    status: str
    timestamp: str
    detail: str


class DeletionResponse(BaseModel):
    """Immediate acknowledgement with tombstone and epoch confirmation per Doc 02 FR-05."""
    deletion_request_id: str
    status: str
    scope: str
    exclusion_epoch: int
    affected_records_count: int
    tombstone_latency_ms: float
    requested_at: datetime
    tombstoned_at: datetime | None = None
    policy_notice: str

    model_config = {"from_attributes": True}


class DeletionDetailResponse(DeletionResponse):
    """Full detail view of deletion progress, stores, timeline, and unlearning metrics."""
    completed_at: datetime | None = None
    certificate_id: str | None = None
    unlearning_time_ms: float | None = None
    retrained_model_version: str | None = None
    affected_shards: list[int] = Field(default_factory=list)
    earliest_affected_slice: int | None = None
    store_checks: dict[str, Any] = Field(default_factory=dict)
    timeline: list[TimelineEvent] = Field(default_factory=list)
    policy_version: str = "1.0"
    error_message: str | None = None


class ExclusionEpochResponse(BaseModel):
    """Current exclusion epoch for dataset fencing."""
    scope: str
    epoch: int
    updated_at: datetime
