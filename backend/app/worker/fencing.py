"""
Training-Job Race Prevention & Fencing Protocol (RC2).

Implements commit-time fencing tokens and exclusion epoch checks per Doc 01 (§14) & Doc 03 (§9).
Guarantees that a training job that started with an obsolete epoch or whose lease expired
is fenced and prevented from committing stale artifacts.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
import time
from typing import Any
import uuid


class StaleJobFencingError(Exception):
    """Raised when a worker attempts to commit with a stale exclusion epoch or expired lease."""
    pass


@dataclass
class FencingToken:
    """Fencing credential issued to a training worker at job initialization."""
    token_id: str
    job_id: str
    exclusion_epoch: int
    issued_at: float
    lease_duration_sec: float
    dataset_manifest_hash: str

    def is_expired(self) -> bool:
        """Returns True if the worker lease has expired without renewal."""
        return (time.time() - self.issued_at) > self.lease_duration_sec


class FencingManager:
    """
    Coordinates worker fencing tokens and tracks stale commit attempts.
    Target: PostRequestCommitCount = 0 per Doc 08 §17.
    """

    def __init__(self):
        self.active_tokens: dict[str, FencingToken] = {}
        self.stale_jobs_rejected: int = 0
        self.successful_commits: int = 0

    def issue_token(
        self,
        job_id: str,
        current_epoch: int,
        dataset_manifest_hash: str,
        lease_duration_sec: float = 300.0,
    ) -> FencingToken:
        """Issues a new fencing token bound to the current exclusion epoch."""
        token_id = f"fence_{uuid.uuid4().hex[:12]}"
        token = FencingToken(
            token_id=token_id,
            job_id=job_id,
            exclusion_epoch=current_epoch,
            issued_at=time.time(),
            lease_duration_sec=lease_duration_sec,
            dataset_manifest_hash=dataset_manifest_hash,
        )
        self.active_tokens[token_id] = token
        return token

    def renew_lease(self, token_id: str, additional_sec: float = 300.0) -> bool:
        """Renews the heartbeat lease for an active worker."""
        if token_id in self.active_tokens:
            self.active_tokens[token_id].issued_at = time.time()
            self.active_tokens[token_id].lease_duration_sec = additional_sec
            return True
        return False

    def validate_pre_read(self, token: FencingToken, current_epoch: int) -> None:
        """Check 1: Validate before reading records into memory."""
        if token.exclusion_epoch != current_epoch:
            self.stale_jobs_rejected += 1
            raise StaleJobFencingError(
                f"Pre-read fence triggered: Worker epoch {token.exclusion_epoch} is obsolete. Current epoch is {current_epoch}."
            )

    def validate_slice_boundary(self, token: FencingToken, current_epoch: int, slice_id: int) -> None:
        """Check 2: Validate at slice boundaries during training."""
        if token.exclusion_epoch != current_epoch:
            self.stale_jobs_rejected += 1
            raise StaleJobFencingError(
                f"Mid-slice fence triggered at slice {slice_id}: Epoch changed from {token.exclusion_epoch} to {current_epoch}."
            )

    def validate_commit(self, token: FencingToken, current_epoch: int) -> None:
        """
        Check 3: Final barrier before publishing checkpoints or promoting model.
        Must be checked in the same transaction or immediately before atomic pointer update.
        """
        if token.is_expired():
            self.stale_jobs_rejected += 1
            raise StaleJobFencingError(
                f"Commit fence triggered: Worker lease expired ({token.lease_duration_sec}s)."
            )

        if token.exclusion_epoch != current_epoch:
            self.stale_jobs_rejected += 1
            raise StaleJobFencingError(
                f"Commit fence triggered: Stale worker epoch {token.exclusion_epoch} vs current {current_epoch}. Commit blocked."
            )

        self.successful_commits += 1

    def get_stats(self) -> dict[str, Any]:
        return {
            "active_tokens_count": len(self.active_tokens),
            "stale_jobs_rejected": self.stale_jobs_rejected,
            "successful_commits": self.successful_commits,
        }


# Global singleton
fencing_manager = FencingManager()
