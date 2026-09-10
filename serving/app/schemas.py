from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ClickEvent(BaseModel):
    """A single observed click, fed in live (e.g. from Kafka/Redis stream
    consumer, or Anushka/Nisha/Vedant's simulated user-interaction feed)."""

    user_id: str
    news_id: str
    time: Optional[datetime] = Field(
        default=None,
        description="Defaults to server time if not provided.",
    )


class RecommendRequest(BaseModel):
    user_id: str
    candidate_news_ids: List[str] = Field(
        ...,
        min_length=1,
        description="Pool of candidate news IDs to rank for this user.",
    )
    top_k: int = Field(default=10, ge=1, le=100)
    # Optional: history for a brand-new / simulated user who isn't in the
    # original MIND behaviors.tsv. If omitted, falls back to any known
    # long-term history + live click-store history for this user_id.
    history: Optional[List[str]] = None


class RankedNews(BaseModel):
    news_id: str
    score: float


class RecommendResponse(BaseModel):
    user_id: str
    recommendations: List[RankedNews]
    model_version: str
    used_long_term: bool
    used_short_term: bool


class ClickAck(BaseModel):
    status: str
    user_id: str
    news_id: str
    total_clicks_for_user: int
