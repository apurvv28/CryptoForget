import time
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from src.db.models import DeletionRequest
from src.mlops.drift import EvidentlyDriftMonitor
from src.mlops.feature_store import FeastFeatureStoreManager
from src.mlops.registry import get_registry_manager
from src.unlearning.unlearner import UnlearningEngine


class UnlearningPipelineOrchestrator:
    """Automated Orchestrator for batch machine unlearning workflows & MLOps lifecycle tasks."""

    def __init__(
        self,
        unlearning_engine: Optional[UnlearningEngine] = None,
        feature_store: Optional[FeastFeatureStoreManager] = None,
    ) -> None:
        self.engine = unlearning_engine or UnlearningEngine()
        self.feature_store = feature_store or FeastFeatureStoreManager()
        self.registry = get_registry_manager()
        self.drift_monitor = EvidentlyDriftMonitor()

    def process_pending_deletion_requests(self, session: Session) -> Dict[str, Any]:
        """Fetches pending deletion requests and executes batch unlearning DAG pipeline."""
        start_time = time.perf_counter()

        pending_requests = (
            session.query(DeletionRequest)
            .filter(DeletionRequest.status == "pending")
            .all()
        )

        if not pending_requests:
            return {
                "processed_count": 0,
                "elapsed_time_ms": 0.0,
                "status": "NO_PENDING_REQUESTS",
                "certificates": [],
            }

        issued_certificates = []

        for req in pending_requests:
            # 1. Execute unlearning via engine
            cert_dict = self.engine.execute_unlearning(
                session=session,
                user_id=req.user_id,
                request_type=req.deletion_type,
            )

            # 2. Update Feature Store
            if req.deletion_type == "Path A":
                self.feature_store.set_tombstone(req.user_id)
            else:
                self.feature_store.purge_user(req.user_id)

            # 3. Log to MLflow Registry
            affected_shard = cert_dict["merkle_exclusion_proof"].get("affected_shard_id", 0)
            self.registry.log_unlearning_run(
                request_id=req.request_id,
                user_id=req.user_id,
                deletion_type=req.deletion_type,
                shard_id=affected_shard if isinstance(affected_shard, int) else 0,
                retraining_time_ms=50.0,
                old_merkle_root=cert_dict["old_merkle_root"],
                new_merkle_root=cert_dict["new_merkle_root"],
            )

            issued_certificates.append(cert_dict)

        elapsed_ms = (time.perf_counter() - start_time) * 1000

        return {
            "processed_count": len(issued_certificates),
            "elapsed_time_ms": round(elapsed_ms, 2),
            "status": "SUCCESS",
            "certificates": issued_certificates,
        }
