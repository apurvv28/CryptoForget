import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db.database import drop_db, get_db_session, init_db
from src.unlearning.mia import MembershipInferenceAttackHarness
from src.unlearning.scrubbing import scrub_user_profile
from src.unlearning.sharded_trainer import ShardedRecommenderEnsemble
from src.unlearning.sisa import SISAPartitioner, hash_user_to_shard
from src.unlearning.unlearner import UnlearningEngine
import numpy as np


def test_sisa_partitioner():
    partitioner = SISAPartitioner(num_shards=5)
    user_data = {
        "U1000": ["N1", "N2"],
        "U1001": ["N3", "N4"],
        "U1002": ["N5"],
    }
    partitioner.populate_from_histories(user_data)
    stats = partitioner.get_shard_stats()
    assert sum(stats.values()) == 3

    shard_id, was_found = partitioner.remove_user("U1000")
    assert was_found is True
    assert "U1000" not in partitioner.get_shard_histories(shard_id)


def test_sharded_ensemble_selective_retraining():
    ensemble = ShardedRecommenderEnsemble(num_shards=5)
    ensemble.load_base_artifacts()

    # Retrain single shard
    retrain_ms = ensemble.retrain_shard(shard_id=0)
    assert retrain_ms >= 0.0

    # Post-training unlearning of user U1000
    shard_id, unlearn_ms, was_found = ensemble.unlearn_user_post_training("U1000")
    assert 0 <= shard_id < 5
    assert unlearn_ms >= 0.0


def test_unlearning_engine_path_a_and_path_b():
    drop_db()
    init_db()

    ensemble = ShardedRecommenderEnsemble(num_shards=5)
    ensemble.load_base_artifacts()
    engine = UnlearningEngine(ensemble=ensemble)

    with get_db_session() as session:
        # Path A Deletion
        cert_a = engine.execute_unlearning(session, user_id="U1000", request_type="Path A")
        assert cert_a["user_id"] == "U1000"
        assert cert_a["deletion_type"] == "Path A"
        assert cert_a["ecdsa_signature"] != ""

        # Path B Deletion
        cert_b = engine.execute_unlearning(session, user_id="U1001", request_type="Path B")
        assert cert_b["user_id"] == "U1001"
        assert cert_b["deletion_type"] == "Path B"
        assert cert_b["ecdsa_signature"] != ""
        assert cert_b["old_merkle_root"] != ""
        assert cert_b["new_merkle_root"] != ""


def test_mia_harness_and_scrubbing():
    harness = MembershipInferenceAttackHarness()
    trained_res = harness.evaluate_user_membership("U1000", ["N1"], is_unlearned=False)
    assert trained_res["mia_success_rate"] > 0.80

    unlearned_res = harness.evaluate_user_membership("U1000", ["N1"], is_unlearned=True)
    assert 0.45 <= unlearned_res["mia_success_rate"] <= 0.55

    # Test profile scrubbing stretch goal
    profile = np.ones(10)
    deleted_vec = np.ones((1, 10)) * 0.5
    scrubbed = scrub_user_profile(profile, deleted_vec)
    assert scrubbed.shape == (10,)
