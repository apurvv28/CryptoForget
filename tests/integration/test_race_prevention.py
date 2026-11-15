"""
Integration Tests for RC2 Race Prevention & Fencing Matrix.

Directly tests the race points specified in Doc 08 (§17):
- Pre-read fence
- Mid-slice fence
- Checkpoint write / commit fence
- Target: PostRequestCommitCount = 0
"""

import pytest

from app.worker.fencing import FencingManager, StaleJobFencingError
from ml.data.exclusion import ExclusionFilter
from ml.data.partitioner import Record


def test_race_point_pre_read():
    """Race Point 1: Deletion request arrives right before worker reads records."""
    fencing = FencingManager()
    token = fencing.issue_token("job_race_1", current_epoch=1, dataset_manifest_hash="h1")

    # Deletion transaction increments epoch
    current_db_epoch = 2

    # Worker checks before reading
    with pytest.raises(StaleJobFencingError):
        fencing.validate_pre_read(token, current_db_epoch)


def test_race_point_mid_slice():
    """Race Point 2: Deletion arrives while training slice 1."""
    fencing = FencingManager()
    token = fencing.issue_token("job_race_2", current_epoch=2, dataset_manifest_hash="h2")

    # Slice 0 boundary: epoch still 2
    fencing.validate_slice_boundary(token, current_epoch=2, slice_id=0)

    # Deletion transaction arrives mid-training: epoch becomes 3
    current_db_epoch = 3

    # Slice 1 boundary: worker checks
    with pytest.raises(StaleJobFencingError):
        fencing.validate_slice_boundary(token, current_db_epoch, slice_id=1)


def test_race_point_commit_time():
    """Race Point 3: Deletion arrives right before model publication."""
    fencing = FencingManager()
    token = fencing.issue_token("job_race_3", current_epoch=3, dataset_manifest_hash="h3")

    # Worker finishes forward/backward passes on obsolete data
    # Right before publish:
    current_db_epoch = 4

    with pytest.raises(StaleJobFencingError):
        fencing.validate_commit(token, current_db_epoch)

    # Post-request commit count is strictly 0
    assert fencing.successful_commits == 0
    assert fencing.stale_jobs_rejected == 1


def test_exclusion_filter_blocks_tombstones():
    """ExclusionFilter strictly strips any tombstoned record from datasets."""
    records = [
        Record("rec_01", "alice", "Alice text 1"),
        Record("rec_02", "bob", "Bob text 1"),
    ]
    tombstones = {"rec_01"}

    retained = ExclusionFilter.filter_records(records, tombstones)
    assert len(retained) == 1
    assert retained[0].record_id == "rec_02"
