"""
SISA Data Partitioner — Deterministic Sharding and Slicing.

Implements subject/user-level partitioning and sequential slicing
with full lineage tracking per Docs 01 (§7), 03 (§5), and 08 (§3).
"""

from dataclasses import dataclass, field
import hashlib
import json
from typing import Any


@dataclass
class Record:
    """Represents a single conversational training sample."""
    record_id: str
    user_id: str
    text: str
    timestamp: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ShardSliceAssignment:
    """Lineage assignment of a record to a shard and slice."""
    record_id: str
    user_id: str
    shard_id: int
    slice_id: int
    record_hash: str


class SISAPartitioner:
    """
    Partitions datasets deterministically into K shards and S slices per shard.

    Ensures subject-level isolation: all records of a specific user are assigned
    to the same shard, minimizing the number of shards affected by a user deletion.
    """

    def __init__(self, num_shards: int = 2, num_slices: int = 3, seed: int = 42):
        if num_shards < 1:
            raise ValueError("num_shards must be at least 1")
        if num_slices < 1:
            raise ValueError("num_slices must be at least 1")
        self.num_shards = num_shards
        self.num_slices = num_slices
        self.seed = seed

    def hash_to_shard(self, user_id: str) -> int:
        """Deterministically map a user_id to a shard index [0, num_shards - 1]."""
        payload = f"{self.seed}:{user_id}".encode("utf-8")
        digest = hashlib.sha256(payload).hexdigest()
        return int(digest[:8], 16) % self.num_shards

    def partition_records(self, records: list[Record]) -> dict[int, dict[int, list[Record]]]:
        """
        Partition records into shards and slices.

        Returns:
            nested dict: shard_id -> slice_id -> list[Record]
        """
        # Group records by user_id
        user_records: dict[str, list[Record]] = {}
        for r in records:
            user_records.setdefault(r.user_id, []).append(r)

        # Initialize structure
        partitioned: dict[int, dict[int, list[Record]]] = {
            s: {sl: [] for sl in range(self.num_slices)}
            for s in range(self.num_shards)
        }

        # Assign each user to a shard
        for user_id, u_recs in sorted(user_records.items(), key=lambda x: x[0]):
            shard_id = self.hash_to_shard(user_id)
            # Distribute the user's records sequentially across slices in that shard
            for idx, r in enumerate(u_recs):
                slice_id = idx % self.num_slices
                partitioned[shard_id][slice_id].append(r)

        return partitioned

    def generate_lineage_index(self, records: list[Record]) -> dict[str, ShardSliceAssignment]:
        """Generate record_id -> ShardSliceAssignment lineage mapping."""
        partitioned = self.partition_records(records)
        lineage: dict[str, ShardSliceAssignment] = {}

        for shard_id, slices in partitioned.items():
            for slice_id, rec_list in slices.items():
                for r in rec_list:
                    h = hashlib.sha256(r.text.encode("utf-8")).hexdigest()
                    lineage[r.record_id] = ShardSliceAssignment(
                        record_id=r.record_id,
                        user_id=r.user_id,
                        shard_id=shard_id,
                        slice_id=slice_id,
                        record_hash=h,
                    )
        return lineage

    def find_affected_shards_and_slices(
        self,
        deleted_record_ids: set[str],
        lineage: dict[str, ShardSliceAssignment],
    ) -> dict[int, int]:
        """
        Given deleted record IDs, find all affected shards and their earliest affected slice.

        Returns:
            dict mapping affected shard_id -> earliest affected slice_id
        """
        affected: dict[int, int] = {}
        for rec_id in deleted_record_ids:
            if rec_id in lineage:
                assignment = lineage[rec_id]
                shard = assignment.shard_id
                current_earliest = affected.get(shard, self.num_slices)
                if assignment.slice_id < current_earliest:
                    affected[shard] = assignment.slice_id
        return affected
