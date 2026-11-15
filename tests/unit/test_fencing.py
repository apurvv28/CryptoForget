"""Unit Tests for Worker Fencing Tokens and Epoch Protection — Phase 5 (RC2)."""

import time
import pytest

from app.worker.fencing import FencingManager, StaleJobFencingError


def test_fencing_token_issue_and_valid_commit():
    """Fencing token validates cleanly when epoch matches and lease is active."""
    manager = FencingManager()
    token = manager.issue_token("job_01", current_epoch=5, dataset_manifest_hash="hash_123")

    # Mid-slice validation passes
    manager.validate_slice_boundary(token, current_epoch=5, slice_id=1)

    # Commit-time validation passes
    manager.validate_commit(token, current_epoch=5)
    assert manager.successful_commits == 1


def test_stale_epoch_blocks_commit():
    """Doc 01 §14: If exclusion epoch increments during training, worker is fenced."""
    manager = FencingManager()
    token = manager.issue_token("job_02", current_epoch=5, dataset_manifest_hash="hash_123")

    # Deletion occurs mid-training, epoch increments to 6
    with pytest.raises(StaleJobFencingError) as exc_info:
        manager.validate_commit(token, current_epoch=6)

    assert "Stale worker epoch 5 vs current 6" in str(exc_info.value)
    assert manager.stale_jobs_rejected == 1


def test_expired_lease_blocks_commit():
    """Doc 01 §14: If worker lease expires without renewal, commit is blocked."""
    manager = FencingManager()
    # Token with 0.05 second lease
    token = manager.issue_token("job_03", current_epoch=5, dataset_manifest_hash="hash_123", lease_duration_sec=0.05)

    time.sleep(0.1)  # wait for lease expiration

    with pytest.raises(StaleJobFencingError) as exc_info:
        manager.validate_commit(token, current_epoch=5)

    assert "Worker lease expired" in str(exc_info.value)
    assert manager.stale_jobs_rejected == 1
