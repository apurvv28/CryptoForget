"""
Baseline Full Trainer — Clean Retraining and Original Baseline (M0 & M1).

Used as the gold-standard comparison against SISA selective unlearning
per Docs 01 (§7), 03 (§5), 04 (§7), and 08 (§2).
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any

import torch
from torch.utils.data import DataLoader
import transformers
from transformers import AutoModelForCausalLM, AutoTokenizer

from ml.data.partitioner import Record
from ml.training.resource_monitor import check_resources
from ml.training.sisa_trainer import TextDataset


@dataclass
class RunManifest:
    """Standardized reproducibility manifest per Doc 04 §7."""
    run_name: str
    run_id: str
    model_id: str
    dataset_version: str
    dataset_manifest_hash: str
    seed: int
    epochs: int
    learning_rate: float
    max_seq_length: int
    batch_size: int
    pytorch_threads: int
    python_version: str
    pytorch_version: str
    transformers_version: str
    platform: str
    wall_time_seconds: float
    total_steps: int
    final_loss: float
    perplexity: float
    peak_rss_gb: float
    artifact_hash: str
    timestamp_utc: str


@dataclass
class BaselineTrainingResult:
    """Telemetry and timing result of a full training/retraining run."""
    run_name: str
    wall_time_seconds: float
    total_steps: int
    final_loss: float
    perplexity: float
    peak_rss_gb: float
    manifest_hash: str
    model_path: Path
    run_manifest: RunManifest


class BaselineTrainer:
    """
    Trains a causal LM from scratch (using the pinned pretrained checkpoint)
    on the full dataset (M0) or retained dataset (M1).
    """

    def __init__(
        self,
        model_path: str = "./models/distilgpt2",
        output_dir: str = "./data/checkpoints/baseline",
        learning_rate: float = 5e-5,
        epochs: int = 1,
        max_seq_length: int = 128,
        seed: int = 42,
    ):
        self.model_path = Path(model_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.max_seq_length = max_seq_length
        self.seed = seed

        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _load_base_model(self) -> AutoModelForCausalLM:
        torch.manual_seed(self.seed)
        model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
        model.to("cpu")
        model.train()
        return model

    def train(
        self,
        records: list[Record],
        run_name: str = "full_retrain",
        dataset_version: str = "v1.0",
        dataset_manifest_hash: str = "",
        sync_to_s3: bool = False,
    ) -> tuple[AutoModelForCausalLM, BaselineTrainingResult]:
        """
        Executes full fine-tuning on the given records and writes a reproducible run manifest.
        """
        start_time = time.perf_counter()
        model = self._load_base_model()
        optimizer = torch.optim.AdamW(model.parameters(), lr=self.learning_rate)

        texts = [r.text for r in records]
        dataset = TextDataset(texts, self.tokenizer, max_length=self.max_seq_length)
        loader = DataLoader(dataset, batch_size=1, shuffle=False)

        total_steps = 0
        total_loss = 0.0

        if not dataset_manifest_hash:
            record_hashes = sorted(hashlib.sha256(r.text.encode()).hexdigest() for r in records)
            dataset_manifest_hash = hashlib.sha256("".join(record_hashes).encode()).hexdigest()

        print(f"\n[Baseline Trainer: {run_name}] Training on {len(records)} records (Seed: {self.seed})...")

        for epoch in range(self.epochs):
            for batch in loader:
                check_resources()
                optimizer.zero_grad()
                outputs = model(
                    input_ids=batch["input_ids"],
                    attention_mask=batch["attention_mask"],
                    labels=batch["labels"],
                )
                loss = outputs.loss
                loss.backward()
                optimizer.step()

                total_steps += 1
                total_loss += loss.item()

        wall_time = time.perf_counter() - start_time
        res_stats = check_resources()
        avg_loss = total_loss / max(1, total_steps)
        import math
        ppl = round(math.exp(min(100.0, avg_loss)), 2)

        # Save model checkpoint
        save_path = self.output_dir / f"{run_name}_seed_{self.seed}.pt"
        torch.save(model.state_dict(), save_path)

        # Hash model checkpoint artifact
        artifact_hash = hashlib.sha256(save_path.read_bytes()).hexdigest()

        # Build standardized Run Manifest (Doc 04 §7)
        run_id = f"{run_name}_{int(time.time())}"
        manifest = RunManifest(
            run_name=run_name,
            run_id=run_id,
            model_id=str(self.model_path),
            dataset_version=dataset_version,
            dataset_manifest_hash=dataset_manifest_hash,
            seed=self.seed,
            epochs=self.epochs,
            learning_rate=self.learning_rate,
            max_seq_length=self.max_seq_length,
            batch_size=1,
            pytorch_threads=torch.get_num_threads(),
            python_version=platform.python_version(),
            pytorch_version=torch.__version__,
            transformers_version=transformers.__version__,
            platform=f"{platform.system()} {platform.release()}",
            wall_time_seconds=round(wall_time, 2),
            total_steps=total_steps,
            final_loss=round(avg_loss, 4),
            perplexity=ppl,
            peak_rss_gb=res_stats["rss_gb"],
            artifact_hash=artifact_hash,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )

        manifest_path = self.output_dir / f"{run_name}_seed_{self.seed}_manifest.json"
        manifest_path.write_text(json.dumps(asdict(manifest), indent=2))

        # Optional S3 Sync
        if sync_to_s3:
            try:
                from app.services.s3_service import s3_service
                s3_service.upload_file(save_path, f"baselines/{save_path.name}")
                s3_service.upload_file(manifest_path, f"baselines/{manifest_path.name}")
                print(f"[Baseline Trainer] Model & manifest synced to S3.")
            except Exception as e:
                print(f"[Baseline Trainer] S3 sync skipped/failed: {e}")

        result = BaselineTrainingResult(
            run_name=run_name,
            wall_time_seconds=wall_time,
            total_steps=total_steps,
            final_loss=avg_loss,
            perplexity=ppl,
            peak_rss_gb=res_stats["rss_gb"],
            manifest_hash=dataset_manifest_hash,
            model_path=save_path,
            run_manifest=manifest,
        )
        print(f"[Baseline Trainer: {run_name}] Completed in {wall_time:.2f}s | Steps: {total_steps} | Loss: {avg_loss:.4f} | PPL: {ppl} | Artifact SHA-256: {artifact_hash[:16]}...\n")
        return model, result
