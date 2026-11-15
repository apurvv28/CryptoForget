"""Unit Tests for Phase 4 SISA Engine & Model Registry."""

import json
from pathlib import Path
import pytest
import torch

from ml.data.partitioner import Record, SISAPartitioner
from ml.inference.engine import InferenceEngine
from ml.registry.model_registry import DeploymentManifest, ModelRegistry
from ml.training.checkpoint import CheckpointManager


@pytest.fixture
def tmp_registry(tmp_path: Path) -> ModelRegistry:
    return ModelRegistry(registry_dir=tmp_path / "registry")


@pytest.fixture
def dummy_checkpoints(tmp_path: Path) -> dict[int, Path]:
    chk_dir = tmp_path / "checkpoints"
    chk_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    for shard in [0, 1]:
        p = chk_dir / f"shard_{shard}_slice_2.pt"
        torch.save({"model_state_dict": {}, "shard_id": shard}, p)
        paths[shard] = p
    return paths


def test_model_registry_registration_and_validation(tmp_registry: ModelRegistry, dummy_checkpoints: dict[int, Path]):
    """Verifies that model candidates are registered and validated cleanly."""
    manifest = tmp_registry.register_version(
        model_version="v1.0.0-test",
        model_type="sisa_ensemble",
        num_shards=2,
        num_slices=3,
        shard_checkpoints=dummy_checkpoints,
        manifest_hash="dummy_hash_123",
    )
    assert manifest.model_version == "v1.0.0-test"
    assert manifest.validation_passed is True
    assert (tmp_registry.versions_dir / "v1.0.0-test.json").is_file()


def test_atomic_promotion_and_rollback(tmp_registry: ModelRegistry, dummy_checkpoints: dict[int, Path]):
    """Verifies zero-downtime atomic promotion and safe rollback."""
    # 1. Register and promote version 1
    tmp_registry.register_version(
        model_version="v1.0.0",
        model_type="sisa_ensemble",
        num_shards=2,
        num_slices=3,
        shard_checkpoints=dummy_checkpoints,
        manifest_hash="hash_v1",
    )
    m1 = tmp_registry.promote_version("v1.0.0")
    assert m1.status == "active"
    assert tmp_registry.get_current_deployment().model_version == "v1.0.0"

    # 2. Register and promote version 2
    tmp_registry.register_version(
        model_version="v1.0.1",
        model_type="sisa_ensemble",
        num_shards=2,
        num_slices=3,
        shard_checkpoints=dummy_checkpoints,
        manifest_hash="hash_v2",
    )
    m2 = tmp_registry.promote_version("v1.0.1")
    assert m2.status == "active"
    assert m2.previous_version == "v1.0.0"
    assert tmp_registry.get_current_deployment().model_version == "v1.0.1"

    # 3. Rollback to version 1
    rolled = tmp_registry.rollback()
    assert rolled is not None
    assert rolled.model_version == "v1.0.0"
    assert tmp_registry.get_current_deployment().model_version == "v1.0.0"


def test_unaffected_shards_not_retrained():
    """Doc 03 §5: Verify that only the shard containing deleted user is identified as affected."""
    partitioner = SISAPartitioner(num_shards=2, num_slices=3, seed=42)
    records = [
        Record("rec_01", "alice", "Alice text 1"),
        Record("rec_02", "alice", "Alice text 2"),
        Record("rec_03", "bob", "Bob text 1"),
    ]
    lineage = partitioner.generate_lineage_index(records)
    # Alice requests deletion
    affected = partitioner.find_affected_shards_and_slices({"rec_01"}, lineage)

    # Shard for alice should be in affected, but Bob's shard should NOT be affected
    alice_shard = lineage["rec_01"].shard_id
    bob_shard = lineage["rec_03"].shard_id
    assert alice_shard in affected
    if alice_shard != bob_shard:
        assert bob_shard not in affected
