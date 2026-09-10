import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import joblib
import pandas as pd

# Make the project's `src` package importable inside the container.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models.dynamic_recommender import DynamicRecommender
from src.personalization.history_profile import EventDynamicProfileBuilder
from src.personalization.user_click_store import UserClickStore

MODEL_VERSION = os.getenv("MODEL_VERSION", "dev")
MODELS_DIR = Path(
    os.getenv(
        "MODELS_DIR",
        str(Path(__file__).resolve().parents[1] / "models"),
    )
)

ALPHA = float(os.getenv("ALPHA", "0.5"))
SHORT_TERM_WINDOW_HOURS = float(os.getenv("SHORT_TERM_WINDOW_HOURS", "24"))
DECAY_RATE = float(os.getenv("DECAY_RATE", "0.05"))


class RecommenderService:
    """Holds the loaded content model + live click store, and answers
    /recommend and /clicks requests. Instantiated once at app startup."""

    def __init__(self) -> None:
        content_model_path = MODELS_DIR / "content_model.joblib"
        user_histories_path = MODELS_DIR / "user_histories.joblib"

        if not content_model_path.exists():
            raise FileNotFoundError(
                f"{content_model_path} not found. Run "
                "scripts/build_content_model.py first (or mount the "
                "models/ volume) before starting the API."
            )

        self.content_model = joblib.load(content_model_path)

        self.user_histories: Dict[str, List[str]] = (
            joblib.load(user_histories_path)
            if user_histories_path.exists()
            else {}
        )

        self.profile_builder = EventDynamicProfileBuilder(
            content_model=self.content_model,
            alpha=ALPHA,
            short_term_window_hours=SHORT_TERM_WINDOW_HOURS,
            decay_rate=DECAY_RATE,
        )

        self.recommender = DynamicRecommender(content_model=self.content_model)

        # In-memory live click store. In production this would be backed by
        # Redis/Kafka state (Anushka's streaming layer) instead of RAM, but
        # the interface below stays the same either way.
        self.click_store = UserClickStore()

    def record_click(self, user_id: str, news_id: str, time: Optional[datetime]) -> int:
        ts = time or datetime.now(timezone.utc)
        self.click_store.add_click(user_id=user_id, news_id=news_id, timestamp=ts)
        return self.click_store.get_click_count(user_id)

    def _timestamped_interactions(self, user_id: str) -> pd.DataFrame:
        clicks = self.click_store.get_clicks(user_id)
        if not clicks:
            return pd.DataFrame(columns=["user_id", "time", "news_id", "clicked"])
        return pd.DataFrame(clicks)

    def recommend(
        self,
        user_id: str,
        candidate_news_ids: List[str],
        top_k: int,
        history_override: Optional[List[str]] = None,
    ):
        history_list = (
            history_override
            if history_override is not None
            else self.user_histories.get(user_id, [])
        )
        history_str = " ".join(history_list) if history_list else ""

        timestamped_interactions = self._timestamped_interactions(user_id)
        reference_time = datetime.now(timezone.utc)

        dynamic_profile = self.profile_builder.build_profile(
            history=history_str,
            timestamped_interactions=timestamped_interactions,
            reference_time=reference_time,
        )

        ranked = self.recommender.rank(
            dynamic_profile=dynamic_profile,
            news_ids=candidate_news_ids,
        )

        return {
            "ranked": ranked[:top_k],
            "used_long_term": bool(history_list),
            "used_short_term": not timestamped_interactions.empty,
        }


# Loaded once, reused across requests.
service: Optional[RecommenderService] = None


def get_service() -> RecommenderService:
    global service
    if service is None:
        service = RecommenderService()
    return service
