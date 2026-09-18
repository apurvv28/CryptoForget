import hashlib
import os
import time
from typing import Any, Dict, Optional

import mlflow

from src.config import MLFLOW_TRACKING_URI, MODEL_VERSION


class MLflowRegistryManager:
    """MLflow experiment tracking and model registry manager for sharded unlearning runs."""

    def __init__(self, tracking_uri: str = MLFLOW_TRACKING_URI) -> None:
        self.tracking_uri = tracking_uri
        mlflow.set_tracking_uri(self.tracking_uri)
        self.experiment_name = "CryptoForget_Unlearning_Pipeline"
        mlflow.set_experiment(self.experiment_name)

    def log_unlearning_run(
        self,
        request_id: str,
        user_id: str,
        deletion_type: str,
        shard_id: int,
        retraining_time_ms: float,
        old_merkle_root: str,
        new_merkle_root: str,
        mia_success_rate: float = 0.50,
        utility_auc: float = 0.98,
    ) -> Dict[str, Any]:
        """Logs an unlearning retraining run to MLflow."""
        run_name = f"Unlearn-{deletion_type}-Shard{shard_id}-{user_id[:6]}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log Parameters
            mlflow.log_param("request_id", request_id)
            mlflow.log_param("user_id", user_id)
            mlflow.log_param("deletion_type", deletion_type)
            mlflow.log_param("affected_shard_id", shard_id)
            mlflow.log_param("old_merkle_root", old_merkle_root)
            mlflow.log_param("new_merkle_root", new_merkle_root)

            # Log Metrics
            mlflow.log_metric("retraining_time_ms", retraining_time_ms)
            mlflow.log_metric("mia_privacy_success_rate", mia_success_rate)
            mlflow.log_metric("model_utility_auc", utility_auc)

            # Generate SHA-256 model version hash
            raw_hash_content = f"{run.info.run_id}:{new_merkle_root}:{shard_id}"
            model_hash = hashlib.sha256(raw_hash_content.encode("utf-8")).hexdigest()
            mlflow.log_param("model_version_hash", model_hash)

            run_id = run.info.run_id

        return {
            "run_id": run_id,
            "model_version_hash": model_hash,
            "experiment_name": self.experiment_name,
            "timestamp": time.time(),
        }

    def get_latest_registered_version(self) -> Dict[str, Any]:
        """Returns the latest logged model version details."""
        experiment = mlflow.get_experiment_by_name(self.experiment_name)
        if not experiment:
            return {
                "model_version": MODEL_VERSION,
                "model_hash": "GENESIS_MODEL_HASH",
                "run_id": None,
            }

        runs = mlflow.search_runs(
            experiment_ids=[experiment.experiment_id],
            max_results=1,
            order_by=["attribute.start_time DESC"],
        )

        if runs.empty:
            return {
                "model_version": MODEL_VERSION,
                "model_hash": "GENESIS_MODEL_HASH",
                "run_id": None,
            }

        latest_run = runs.iloc[0]
        return {
            "model_version": MODEL_VERSION,
            "model_hash": latest_run.get("params.model_version_hash", "GENESIS_MODEL_HASH"),
            "run_id": latest_run.get("run_id"),
        }


# Singleton instance
_registry_manager_instance = None


def get_registry_manager() -> MLflowRegistryManager:
    global _registry_manager_instance
    if _registry_manager_instance is None:
        _registry_manager_instance = MLflowRegistryManager()
    return _registry_manager_instance
