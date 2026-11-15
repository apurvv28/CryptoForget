"""Chat Request and Response Schemas — Phase 1."""

from datetime import datetime
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Chat message request."""
    prompt: str = Field(..., min_length=1, max_length=2000, description="User prompt")
    conversation_id: int | None = Field(default=None, description="Optional conversation ID")
    max_new_tokens: int = Field(default=50, ge=1, le=150, description="Tokens to generate")
    temperature: float = Field(default=0.7, ge=0.1, le=2.0, description="Sampling temperature")


class ChatResponse(BaseModel):
    """Chat message response."""
    response: str
    model_version: str = "distilgpt2-82M"
    conversation_id: int | None = None
    prompt_tokens: int = 0
    generated_tokens: int = 0
    inference_time_ms: float = 0.0


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model_version: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    messages: list[MessageOut] = []

    model_config = {"from_attributes": True}
