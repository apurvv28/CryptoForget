"""Consent and Data Inventory Schemas — Phase 2."""

from datetime import datetime
from pydantic import BaseModel, Field


class ConsentUpdateRequest(BaseModel):
    """User request to grant or withdraw training consent."""
    training_consent: bool = Field(..., description="True to opt-in, False to withdraw")
    purpose: str = Field(default="model_training", description="Consent purpose")
    policy_version: str = Field(default="1.0", description="Privacy notice version")


class ConsentEventOut(BaseModel):
    """Immutable consent audit record."""
    id: int
    status: str
    purpose: str
    scope: str
    policy_version: str
    effective_timestamp: datetime
    audit_hash: str

    model_config = {"from_attributes": True}


class ConsentStatusResponse(BaseModel):
    """Current effective consent status for the user/session."""
    training_consent: bool = False
    purpose: str = "model_training"
    scope: str = "conversational_ai_finetuning"
    policy_version: str = "1.0"
    last_updated: datetime | None = None
    events_count: int = 0
    history: list[ConsentEventOut] = []


class DataCategoryInventory(BaseModel):
    category: str
    purpose: str
    storage_location: str
    retention_period: str
    training_eligible: bool
    count: int


class DataInventoryResponse(BaseModel):
    """Transparent summary of stored and training-eligible data per Doc 02 FR-04."""
    total_messages_stored: int
    training_eligible_messages: int
    messages_used_in_model: int
    training_consent_active: bool
    categories: list[DataCategoryInventory]
    policy_version: str = "1.0"
