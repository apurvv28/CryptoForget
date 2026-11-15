"""
Exclusion Manifest and Epoch-Based Data Filtering (RC2).

Per Doc 01 (§8, §14):
Filters tombstoned records from dataset manifests and validates
that no worker commits artifacts trained on obsolete epochs.
"""

from typing import Iterable
from ml.data.partitioner import Record
from backend.app.worker.fencing import StaleJobFencingError


class ExclusionFilter:
    """Filters records against active tombstones and exclusion epochs."""

    @staticmethod
    def filter_records(
        records: list[Record],
        tombstoned_record_ids: set[str],
    ) -> list[Record]:
        """Excludes any record currently marked with a durable tombstone."""
        return [r for r in records if r.record_id not in tombstoned_record_ids]

    @staticmethod
    def assert_epoch_current(
        worker_epoch: int,
        active_db_epoch: int,
        checkpoint_stage: str = "read",
    ) -> None:
        """
        Validates exclusion epoch consistency.
        Raises StaleJobFencingError if epoch changed during job execution.
        """
        if worker_epoch != active_db_epoch:
            raise StaleJobFencingError(
                f"Fencing violation at stage '{checkpoint_stage}': "
                f"Worker started with exclusion epoch {worker_epoch}, but current active epoch is {active_db_epoch}. "
                f"Tombstones have been committed since job started. Publication blocked."
            )
