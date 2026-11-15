"""
Model Registry — Versioning, Atomic Promotion, and Safe Rollback.

Implements deployment immutability and atomic manifest pointer switching
per Docs 01 (§6, §7), 03 (§4), and 06 (§9).
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any

import torch
from transformers import AutoModelForCausalLM


@dataclass
class DeploymentManifest:
    """Specification of an actively deployed model or SISA ensemble."""
    model_version: str
    model_type: str  # "sisa_ensemble" or "single_baseline"
    num_shards: int
    num_slices: int
    shard_checkpoints: dict[int, str]  # shard_id -> checkpoint file path
    manifest_hash: str
    validation_passed: bool
    promoted_at: str
    status: str = "active"  # "active" | "retired" | "rolled_back"
    previous_version: str | None = None
    extra_metadata: dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """
    Manages production model deployments with atomic pointer switching,
    immutable version directories, and automatic rollback capabilities.
    """

    def __init__(
        self,
        registry_dir: Path | str = "./data/registry",
        base_model_path: str = "./models/distilgpt2",
    ):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir = self.registry_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.base_model_path = Path(base_model_path)
        self.pointer_file = self.registry_dir / "current_deployment.json"

    def register_version(
        self,
        model_version: str,
        model_type: str,
        num_shards: int,
        num_slices: int,
        shard_checkpoints: dict[int, str | Path],
        manifest_hash: str,
        extra_metadata: dict[str, Any] | None = None,
    ) -> DeploymentManifest:
        """
        Registers a new model version candidate. Validates checkpoints before storing.
        """
        # Validate that all shard checkpoints exist and are non-empty
        validated_paths: dict[int, str] = {}
        for shard_id, chk_path in shard_checkpoints.items():
            path_obj = Path(chk_path)
            if not path_obj.is_file() or path_obj.stat().st_size == 0:
                raise FileNotFoundError(f"Invalid or missing checkpoint for shard {shard_id}: {chk_path}")
            validated_paths[int(shard_id)] = str(path_obj.resolve())

        # Determine current active version to link previous pointer
        curr = self.get_current_deployment()
        prev_ver = curr.model_version if curr else None

        manifest = DeploymentManifest(
            model_version=model_version,
            model_type=model_type,
            num_shards=num_shards,
            num_slices=num_slices,
            shard_checkpoints=validated_paths,
            manifest_hash=manifest_hash,
            validation_passed=True,
            promoted_at=datetime.now(timezone.utc).isoformat(),
            status="staged",
            previous_version=prev_ver,
            extra_metadata=extra_metadata or {},
        )

        version_manifest_path = self.versions_dir / f"{model_version}.json"
        version_manifest_path.write_text(json.dumps(asdict(manifest), indent=2))
        return manifest

    def validate_deployment(self, manifest: DeploymentManifest) -> bool:
        """
        Smoke-tests model artifact integrity by loading weights into CPU RAM.
        """
        try:
            for shard_id, path_str in manifest.shard_checkpoints.items():
                chk = torch.load(path_str, map_location="cpu", weights_only=False)
                if "model_state_dict" not in chk:
                    return False
            return True
        except Exception as e:
            print(f"[ModelRegistry] Validation failed for {manifest.model_version}: {e}")
            return False

    def promote_version(
        self,
        model_version: str,
        sync_to_s3: bool = False,
    ) -> DeploymentManifest:
        """
        Atomically switches the active deployment pointer to the specified model version.
        Guarantees zero-downtime atomic pointer switch via tempfile + move per Doc 03 §4.
        """
        version_file = self.versions_dir / f"{model_version}.json"
        if not version_file.is_file():
            raise ValueError(f"Version {model_version} does not exist in registry.")

        data = json.loads(version_file.read_text())
        manifest = DeploymentManifest(**data)

        # Run integrity validation
        if not self.validate_deployment(manifest):
            raise RuntimeError(f"Deployment validation failed for version {model_version}")

        manifest.status = "active"
        manifest.promoted_at = datetime.now(timezone.utc).isoformat()

        # Write to temporary file, then rename atomically
        with tempfile.NamedTemporaryFile(dir=str(self.registry_dir), delete=False, suffix=".tmp") as tmp:
            tmp_path = Path(tmp.name)
            tmp_path.write_text(json.dumps(asdict(manifest), indent=2))

        shutil.move(str(tmp_path), str(self.pointer_file))
        version_file.write_text(json.dumps(asdict(manifest), indent=2))

        print(f"[ModelRegistry] Successfully promoted {model_version} (Active)")

        if sync_to_s3:
            try:
                from app.services.s3_service import s3_service
                s3_service.upload_file(self.pointer_file, "deployments/current_deployment.json")
                s3_service.upload_file(version_file, f"deployments/versions/{model_version}.json")
            except Exception as e:
                print(f"[ModelRegistry] S3 sync skipped/failed: {e}")

        return manifest

    def rollback(self) -> DeploymentManifest | None:
        """
        Rolls back to the previous known-good deployment version per Doc 03 §11.
        """
        current = self.get_current_deployment()
        if not current or not current.previous_version:
            print("[ModelRegistry] No previous deployment version available for rollback.")
            return None

        prev_version = current.previous_version
        print(f"[ModelRegistry] Rolling back from {current.model_version} to {prev_version}...")
        return self.promote_version(prev_version)

    def get_active_version(self) -> str | None:
        """Returns the model version string of the currently active deployment."""
        curr = self.get_current_deployment()
        return curr.model_version if curr else None

    def get_current_deployment(self) -> DeploymentManifest | None:
        """Reads the currently active deployment manifest."""
        if not self.pointer_file.is_file():
            return None
        try:
            data = json.loads(self.pointer_file.read_text())
            return DeploymentManifest(**data)
        except Exception:
            return None


# Global singleton
model_registry = ModelRegistry()
