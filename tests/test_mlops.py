import sys
from pathlib import Path

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.database import drop_db, get_db_session, init_db
from src.db.models import DeletionRequest, User
from src.mlops.drift import EvidentlyDriftMonitor
from src.mlops.feature_store import FeastFeatureStoreManager
from src.mlops.orchestrator import UnlearningPipelineOrchestrator
from src.mlops.registry import MLflowRegistryManager


def test_mlflow_registry_manager():
    manager = MLflowRegistryManager()
    run_info = manager.log_unlearning_run(
        request_id="REQ-TEST1",
        user_id="U1000",
        deletion_type="Path B",
        shard_id=1,
        retraining_time_ms=45.2,
        old_merkle_root="ROOT_OLD_123",
        new_merkle_root="ROOT_NEW_456",
        mia_success_rate=0.50,
    )
    assert run_info["run_id"] is not None
    assert run_info["model_version_hash"] != ""

    latest = manager.get_latest_registered_version()
    assert latest["model_hash"] == run_info["model_version_hash"]


def test_feast_feature_store_manager():
    store = FeastFeatureStoreManager()
    store.register_user_profile(user_id="U1000", history=["N1", "N2"], shard_id=0)

    features = store.get_online_user_features("U1000")
    assert features["user_id"] == "U1000"
    assert features["history"] == ["N1", "N2"]
    assert features.get("use_fallback") is not True

    # Path A Tombstoning
    store.set_tombstone("U1000")
    assert store.is_tombstoned("U1000") is True

    tombstoned_features = store.get_online_user_features("U1000")
    assert tombstoned_features["use_fallback"] is True

    # Path B Purging
    store.purge_user("U1000")
    assert store.is_tombstoned("U1000") is False


def test_evidently_drift_monitor():
    monitor = EvidentlyDriftMonitor(drift_threshold=0.05)
    ref_df = pd.DataFrame({"click_count": [10, 12, 11, 15, 9]})
    cur_df = pd.DataFrame({"click_count": [10, 11, 12, 14, 10]})

    report = monitor.compute_data_drift_report(ref_df, cur_df)
    assert "dataset_drift" in report
    assert report["status"] == "PASS"


def test_unlearning_pipeline_orchestrator():
    drop_db()
    init_db()

    with get_db_session() as session:
        # Create user and pending deletion request
        user = User(user_id="U1005", consent_status=True, shard_id=2)
        session.add(user)

        del_req = DeletionRequest(
            request_id="REQ-ORCH-1",
            user_id="U1005",
            deletion_type="Path B",
            status="pending",
        )
        session.add(del_req)
        session.commit()

        orchestrator = UnlearningPipelineOrchestrator()
        result = orchestrator.process_pending_deletion_requests(session)

        assert result["processed_count"] == 1
        assert result["status"] == "SUCCESS"
        assert len(result["certificates"]) == 1
        assert result["certificates"][0]["user_id"] == "U1005"
