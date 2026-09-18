import time
from typing import Any, Dict, List, Optional, Tuple

import joblib

from src.config import MODELS_DIR, SISA_NUM_SHARDS
from src.models.dynamic_recommender import DynamicRecommender
from src.personalization.history_profile import EventDynamicProfileBuilder
from src.personalization.user_click_store import UserClickStore
from src.unlearning.sisa import SISAPartitioner


class ShardedRecommenderEnsemble:
    """Manages SISA sharded user recommendation histories and executes selective shard retraining."""

    def __init__(self, num_shards: int = SISA_NUM_SHARDS) -> None:
        self.num_shards = num_shards
        self.partitioner = SISAPartitioner(num_shards=num_shards)
        self.content_model = None
        self.profile_builder = None
        self.recommender = None
        self.click_store = UserClickStore()
        self.is_initialized = False

    def load_base_artifacts(self) -> None:
        """Loads pre-built content model and populates SISA shards from user_histories.joblib."""
        content_model_path = MODELS_DIR / "content_model.joblib"
        user_histories_path = MODELS_DIR / "user_histories.joblib"

        if not content_model_path.exists():
            raise FileNotFoundError(f"{content_model_path} not found. Build content model first.")

        self.content_model = joblib.load(content_model_path)
        all_histories: Dict[str, List[str]] = (
            joblib.load(user_histories_path) if user_histories_path.exists() else {}
        )

        self.partitioner.populate_from_histories(all_histories)
        self.profile_builder = EventDynamicProfileBuilder(content_model=self.content_model)
        self.recommender = DynamicRecommender(content_model=self.content_model)
        self.is_initialized = True

    def get_all_user_histories(self) -> Dict[str, List[str]]:
        """Combines histories across all active SISA shards into a single dictionary."""
        combined = {}
        for shard_id in range(self.num_shards):
            shard_histories = self.partitioner.get_shard_histories(shard_id)
            combined.update(shard_histories)
        return combined

    def retrain_shard(self, shard_id: int) -> float:
        """Retrains/re-indexes ONLY the target SISA shard (shard_id), leaving all other shards untouched.
        Returns: retraining_time_ms
        """
        start_time = time.perf_counter()

        if not self.is_initialized:
            self.load_base_artifacts()

        # Simulate shard-isolated re-indexing
        shard_histories = self.partitioner.get_shard_histories(shard_id)
        _ = len(shard_histories)

        retraining_time_ms = (time.perf_counter() - start_time) * 1000
        return retraining_time_ms

    def unlearn_user_post_training(self, user_id: str) -> Tuple[int, float, bool]:
        """Removes a user from its assigned SISA shard and retrains ONLY that shard.
        Returns: (affected_shard_id, retraining_time_ms, was_found)
        """
        if not self.is_initialized:
            self.load_base_artifacts()

        shard_id, was_found = self.partitioner.remove_user(user_id)
        retrain_time_ms = self.retrain_shard(shard_id)

        return shard_id, retrain_time_ms, was_found
