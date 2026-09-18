from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set


class FeastFeatureStoreManager:
    """Feature Store abstraction (Feast compliant) for user profile online serving & tombstoning."""

    def __init__(self) -> None:
        # In-memory online feature view mapping: user_id -> feature_dict
        self.online_features: Dict[str, Dict[str, Any]] = {}
        # Set of tombstoned user IDs
        self.tombstones: Set[str] = set()

    def register_user_profile(
        self,
        user_id: str,
        history: List[str],
        shard_id: int,
        consent_status: bool = True,
    ) -> Dict[str, Any]:
        """Registers or updates a user feature record in the online feature store."""
        features = {
            "user_id": user_id,
            "history": list(history),
            "shard_id": shard_id,
            "consent_status": consent_status,
            "is_tombstoned": user_id in self.tombstones,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.online_features[user_id] = features
        return features

    def set_tombstone(self, user_id: str) -> None:
        """Sets pre-training tombstone flag for user_id (Path A)."""
        self.tombstones.add(user_id)
        if user_id in self.online_features:
            self.online_features[user_id]["is_tombstoned"] = True
            self.online_features[user_id]["consent_status"] = False

    def is_tombstoned(self, user_id: str) -> bool:
        """Returns True if user_id is tombstoned."""
        return user_id in self.tombstones

    def get_online_user_features(self, user_id: str) -> Dict[str, Any]:
        """Retrieves user features for live online recommendation scoring.
        If tombstoned or user is opted out, returns non-personalized fallback profile.
        """
        if user_id in self.tombstones or user_id not in self.online_features:
            return {
                "user_id": user_id,
                "history": [],
                "is_tombstoned": True,
                "use_fallback": True,
            }
        return self.online_features[user_id]

    def purge_user(self, user_id: str) -> bool:
        """Completely purges user features from feature store (Path B)."""
        self.tombstones.discard(user_id)
        if user_id in self.online_features:
            del self.online_features[user_id]
            return True
        return False
