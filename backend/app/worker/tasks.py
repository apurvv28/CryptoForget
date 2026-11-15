"""
Background Worker Tasks and SISA Pipeline Orchestration.

Executes asynchronous training, selective unlearning, and atomic model promotion
per Docs 01 (§6), 02 (FR-07), and 03 (§4).
"""

import asyncio
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
import time
from typing import Any
import uuid

from ml.data.partitioner import Record
from ml.registry.model_registry import model_registry
from ml.training.sisa_trainer import SISATrainer


@dataclass
class BackgroundJob:
    """Represents a background training or unlearning job."""
    job_id: str
    job_type: str  # "sisa_initial_train" | "sisa_unlearn"
    status: str  # "queued" | "running" | "completed" | "failed"
    created_at: str
    started_at: str | None = None
    completed_at: str | None = None
    target_records_count: int = 0
    deleted_records_count: int = 0
    promoted_model_version: str | None = None
    error_message: str | None = None
    metrics: dict[str, Any] = field(default_factory=dict)


class JobWorker:
    """In-process asynchronous job queue and worker for ML training jobs."""

    def __init__(self):
        self.jobs: dict[str, BackgroundJob] = {}
        self._lock = threading.Lock()

    def submit_sisa_initial_training(
        self,
        records: list[Record],
        version_name: str = "v1.0.0-sisa",
        num_shards: int = 2,
        num_slices: int = 3,
    ) -> str:
        """Submits initial SISA training job to the worker."""
        job_id = f"job_init_{uuid.uuid4().hex[:8]}"
        job = BackgroundJob(
            job_id=job_id,
            job_type="sisa_initial_train",
            status="queued",
            created_at=datetime.now(timezone.utc).isoformat(),
            target_records_count=len(records),
        )
        with self._lock:
            self.jobs[job_id] = job

        # Run in separate thread so it doesn't block FastAPI event loop
        thread = threading.Thread(
            target=self._execute_sisa_training,
            args=(job_id, records, version_name, num_shards, num_slices),
            daemon=True,
        )
        thread.start()
        return job_id

    def submit_sisa_unlearning(
        self,
        all_records: list[Record],
        deleted_ids: set[str],
        version_name: str | None = None,
        num_shards: int = 2,
        num_slices: int = 3,
    ) -> str:
        """Submits selective unlearning job."""
        job_id = f"job_unlearn_{uuid.uuid4().hex[:8]}"
        if not version_name:
            version_name = f"v1.0.{len(self.jobs) + 1}-unlearned"

        job = BackgroundJob(
            job_id=job_id,
            job_type="sisa_unlearn",
            status="queued",
            created_at=datetime.now(timezone.utc).isoformat(),
            target_records_count=len(all_records),
            deleted_records_count=len(deleted_ids),
        )
        with self._lock:
            self.jobs[job_id] = job

        thread = threading.Thread(
            target=self._execute_sisa_unlearning,
            args=(job_id, all_records, deleted_ids, version_name, num_shards, num_slices),
            daemon=True,
        )
        thread.start()
        return job_id

    def _execute_sisa_training(
        self,
        job_id: str,
        records: list[Record],
        version_name: str,
        num_shards: int,
        num_slices: int,
    ) -> None:
        """Worker thread executing initial SISA training and promotion."""
        job = self.jobs[job_id]
        job.status = "running"
        job.started_at = datetime.now(timezone.utc).isoformat()

        try:
            trainer = SISATrainer(
                num_shards=num_shards,
                num_slices=num_slices,
            )
            train_res = trainer.initial_train(records)

            # Map active checkpoints (final slice per shard)
            shard_checkpoints = {
                shard_id: Path(f"./data/checkpoints/shard_{shard_id}_slice_{num_slices - 1}.pt")
                for shard_id in range(num_shards)
            }

            # Register version in ModelRegistry
            manifest = model_registry.register_version(
                model_version=version_name,
                model_type="sisa_ensemble",
                num_shards=num_shards,
                num_slices=num_slices,
                shard_checkpoints=shard_checkpoints,
                manifest_hash=train_res.manifest_hash,
                extra_metadata={"job_id": job_id, "steps": train_res.total_steps},
            )

            # Atomically promote
            model_registry.promote_version(version_name, sync_to_s3=True)

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.promoted_model_version = version_name
            job.metrics = {
                "wall_time_sec": round(train_res.wall_time_seconds, 2),
                "steps": train_res.total_steps,
                "peak_rss_gb": train_res.peak_rss_gb,
            }
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"[JobWorker] Job {job_id} failed: {e}")

    def _execute_sisa_unlearning(
        self,
        job_id: str,
        all_records: list[Record],
        deleted_ids: set[str],
        version_name: str,
        num_shards: int,
        num_slices: int,
    ) -> None:
        """Worker thread executing selective unlearning and atomic promotion."""
        job = self.jobs[job_id]
        job.status = "running"
        job.started_at = datetime.now(timezone.utc).isoformat()

        try:
            trainer = SISATrainer(
                num_shards=num_shards,
                num_slices=num_slices,
            )
            unlearn_res = trainer.unlearn(all_records=all_records, deleted_record_ids=deleted_ids)

            shard_checkpoints = {
                shard_id: Path(f"./data/checkpoints/shard_{shard_id}_slice_{num_slices - 1}.pt")
                for shard_id in range(num_shards)
            }

            # Register & promote
            manifest = model_registry.register_version(
                model_version=version_name,
                model_type="sisa_ensemble",
                num_shards=num_shards,
                num_slices=num_slices,
                shard_checkpoints=shard_checkpoints,
                manifest_hash=unlearn_res.manifest_hash,
                extra_metadata={"job_id": job_id, "deleted_count": len(deleted_ids)},
            )
            model_registry.promote_version(version_name, sync_to_s3=True)

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc).isoformat()
            job.promoted_model_version = version_name
            job.metrics = {
                "wall_time_sec": round(unlearn_res.wall_time_seconds, 2),
                "steps": unlearn_res.total_steps,
                "peak_rss_gb": unlearn_res.peak_rss_gb,
            }
        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc).isoformat()
            print(f"[JobWorker] Job {job_id} failed: {e}")

    def get_job_status(self, job_id: str) -> BackgroundJob | None:
        """Returns the current state of a background job."""
        with self._lock:
            return self.jobs.get(job_id)


# Global singleton
job_worker = JobWorker()
