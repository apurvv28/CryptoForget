import hashlib
from typing import Dict, List, Optional, Set, Tuple

from src.config import SISA_NUM_SHARDS, SISA_NUM_SLICES


def hash_user_to_shard(user_id: str, num_shards: int = SISA_NUM_SHARDS) -> int:
    """Deterministically maps a user_id to a SISA shard ID (0 to num_shards-1)."""
    hash_val = int(hashlib.sha256(user_id.encode("utf-8")).hexdigest(), 16)
    return hash_val % num_shards


class SISAPartitioner:
    """SISA (Sharded, Isolated, Sliced, Aggregated) Data Partitioner for user recommendation histories."""

    def __init__(
        self,
        num_shards: int = SISA_NUM_SHARDS,
        num_slices: int = SISA_NUM_SLICES,
    ) -> None:
        self.num_shards = num_shards
        self.num_slices = num_slices
        # Maps shard_id -> Dict[user_id, List[news_ids]]
        self.shards: Dict[int, Dict[str, List[str]]] = {i: {} for i in range(num_shards)}

    def populate_from_histories(self, user_histories: Dict[str, List[str]]) -> None:
        """Populates SISA shards from a dictionary of user_id -> list of clicked news_ids."""
        self.shards = {i: {} for i in range(self.num_shards)}
        for user_id, history in user_histories.items():
            shard_id = hash_user_to_shard(user_id, self.num_shards)
            self.shards[shard_id][user_id] = list(history)

    def get_user_shard_id(self, user_id: str) -> int:
        """Returns the shard ID assigned to a given user_id."""
        return hash_user_to_shard(user_id, self.num_shards)

    def get_shard_histories(self, shard_id: int) -> Dict[str, List[str]]:
        """Returns the user histories assigned to shard_id."""
        if shard_id not in self.shards:
            raise ValueError(f"Invalid shard_id {shard_id}. Expected 0 to {self.num_shards - 1}.")
        return self.shards[shard_id]

    def remove_user(self, user_id: str) -> Tuple[int, bool]:
        """Removes a user_id from its assigned SISA shard.
        Returns: (shard_id, was_found)
        """
        shard_id = self.get_user_shard_id(user_id)
        was_found = False
        if user_id in self.shards[shard_id]:
            del self.shards[shard_id][user_id]
            was_found = True
        return shard_id, was_found

    def get_shard_stats(self) -> Dict[int, int]:
        """Returns a dict mapping shard_id -> count of users in that shard."""
        return {shard_id: len(users) for shard_id, users in self.shards.items()}
