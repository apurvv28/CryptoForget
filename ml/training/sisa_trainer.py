"""
SISA Trainer and Selective Unlearning Engine.

Implements sequential slice training, slice-boundary checkpointing,
and selective retraining of affected shard suffixes per Docs 01 (§7), 03 (§5), 06 (§4).
"""

import copy
from dataclasses import dataclass, field
import hashlib
import time
from pathlib import Path
from typing import Any

import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

from ml.data.partitioner import Record, SISAPartitioner, ShardSliceAssignment
from ml.training.checkpoint import CheckpointManager
from ml.training.resource_monitor import check_resources


# Apply CPU thread guardrails per Doc 06 §3
torch.set_num_threads(3)
torch.set_num_interop_threads(1)


class TextDataset(Dataset):
    """PyTorch Dataset for text sequences."""

    def __init__(self, texts: list[str], tokenizer: Any, max_length: int = 128):
        self.encodings = tokenizer(
            texts,
            truncation=True,
            padding="max_length",
            max_length=max_length,
            return_tensors="pt",
        )

    def __len__(self) -> int:
        return len(self.encodings["input_ids"])

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        item = {key: val[idx] for key, val in self.encodings.items()}
        # For CausalLM, labels are identical to input_ids
        item["labels"] = item["input_ids"].clone()
        return item


@dataclass
class SISATrainingResult:
    """Telemetry and timing result of a SISA training or unlearning run."""
    run_type: str  # "initial_training" or "selective_unlearning"
    wall_time_seconds: float
    total_steps: int
    shards_trained: list[int]
    slices_trained: dict[int, list[int]]  # shard_id -> list of slice_ids retrained
    peak_rss_gb: float
    manifest_hash: str


class SISATrainer:
    """
    SISA Trainer orchestrating isolated shard training, slice checkpoints,
    and targeted retraining upon deletion requests.
    """

    def __init__(
        self,
        model_path: str = "./models/distilgpt2",
        checkpoint_dir: str = "./data/checkpoints",
        num_shards: int = 2,
        num_slices: int = 3,
        learning_rate: float = 5e-5,
        epochs_per_slice: int = 1,
        max_seq_length: int = 128,
        seed: int = 42,
    ):
        self.model_path = Path(model_path)
        self.checkpoint_dir = Path(checkpoint_dir)
        self.num_shards = num_shards
        self.num_slices = num_slices
        self.learning_rate = learning_rate
        self.epochs_per_slice = epochs_per_slice
        self.max_seq_length = max_seq_length
        self.seed = seed

        self.partitioner = SISAPartitioner(num_shards=num_shards, num_slices=num_slices, seed=seed)
        self.checkpoint_manager = CheckpointManager(checkpoint_dir=checkpoint_dir)

        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def _load_base_model(self) -> AutoModelForCausalLM:
        """Loads a fresh instance of the pinned base pretrained model."""
        torch.manual_seed(self.seed)
        model = AutoModelForCausalLM.from_pretrained(str(self.model_path))
        model.to("cpu")
        model.train()
        return model

    def _train_single_slice(
        self,
        model: AutoModelForCausalLM,
        optimizer: torch.optim.Optimizer,
        records: list[Record],
    ) -> tuple[int, float]:
        """Trains a model on a single slice's records. Returns (steps, avg_loss)."""
        if not records:
            return 0, 0.0

        texts = [r.text for r in records]
        dataset = TextDataset(texts, self.tokenizer, max_length=self.max_seq_length)
        # Micro-batch = 1 per Doc 06 §4
        loader = DataLoader(dataset, batch_size=1, shuffle=False)

        total_steps = 0
        total_loss = 0.0

        for _ in range(self.epochs_per_slice):
            for batch in loader:
                # Check hardware limits periodically
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

        avg_loss = total_loss / max(1, total_steps)
        return total_steps, avg_loss

    def initial_train(self, records: list[Record]) -> SISATrainingResult:
        """
        Executes initial full SISA training across all K shards and S slices.
        """
        start_time = time.perf_counter()
        partitioned = self.partitioner.partition_records(records)
        total_steps = 0
        slices_trained: dict[int, list[int]] = {}

        # Compute data manifest hash
        record_hashes = sorted(hashlib.sha256(r.text.encode()).hexdigest() for r in records)
        manifest_hash = hashlib.sha256("".join(record_hashes).encode()).hexdigest()

        print(f"\n[SISA Initial Training] Starting K={self.num_shards} shards, S={self.num_slices} slices...")

        for shard_id in range(self.num_shards):
            print(f" -> Training Shard {shard_id}/{self.num_shards - 1}...")
            model = self._load_base_model()
            optimizer = torch.optim.AdamW(model.parameters(), lr=self.learning_rate)
            slices_trained[shard_id] = []

            for slice_id in range(self.num_slices):
                slice_records = partitioned[shard_id][slice_id]
                steps, loss = self._train_single_slice(model, optimizer, slice_records)
                total_steps += steps
                slices_trained[shard_id].append(slice_id)

                # Save checkpoint at slice boundary
                self.checkpoint_manager.save_slice_checkpoint(
                    shard_id=shard_id,
                    slice_id=slice_id,
                    model=model,
                    optimizer=optimizer,
                    step=total_steps,
                    manifest_hash=manifest_hash,
                )
                print(f"    Shard {shard_id} Slice {slice_id}: {steps} steps, loss={loss:.4f} [checkpoint saved]")

            del model
            del optimizer
            import gc
            gc.collect()

        wall_time = time.perf_counter() - start_time
        res_stats = check_resources()

        result = SISATrainingResult(
            run_type="initial_training",
            wall_time_seconds=wall_time,
            total_steps=total_steps,
            shards_trained=list(range(self.num_shards)),
            slices_trained=slices_trained,
            peak_rss_gb=res_stats["rss_gb"],
            manifest_hash=manifest_hash,
        )
        print(f"[SISA Initial Training] Completed in {wall_time:.2f}s, steps={total_steps}, peak RSS={res_stats['rss_gb']} GB\n")
        return result

    def unlearn(
        self,
        all_records: list[Record],
        deleted_record_ids: set[str],
    ) -> SISATrainingResult:
        """
        Executes SISA selective unlearning:
        1. Identifies affected shards and earliest affected slice.
        2. Retrains ONLY the affected shard suffixes from the checkpoint immediately preceding the earliest affected slice.
        3. Excludes deleted records from the retrained slices.
        4. Leaves unaffected shards completely untouched!
        """
        start_time = time.perf_counter()
        lineage = self.partitioner.generate_lineage_index(all_records)
        affected_map = self.partitioner.find_affected_shards_and_slices(deleted_record_ids, lineage)

        if not affected_map:
            print("[SISA Unlearning] No training records were affected by deletion request.")
            return SISATrainingResult(
                run_type="selective_unlearning",
                wall_time_seconds=0.0,
                total_steps=0,
                shards_trained=[],
                slices_trained={},
                peak_rss_gb=check_resources()["rss_gb"],
                manifest_hash="",
            )

        # Filter out deleted records for retraining
        retained_records = [r for r in all_records if r.record_id not in deleted_record_ids]
        partitioned = self.partitioner.partition_records(retained_records)

        # Retained manifest hash
        record_hashes = sorted(hashlib.sha256(r.text.encode()).hexdigest() for r in retained_records)
        manifest_hash = hashlib.sha256("".join(record_hashes).encode()).hexdigest()

        print(f"\n[SISA Selective Unlearning] Affected shards: {list(affected_map.keys())}")
        total_steps = 0
        slices_trained: dict[int, list[int]] = {}

        for shard_id, earliest_slice in affected_map.items():
            print(f" -> Shard {shard_id}: Earliest affected slice = {earliest_slice}. Retraining slices [{earliest_slice}..{self.num_slices - 1}]")
            model = self._load_base_model()
            optimizer = torch.optim.AdamW(model.parameters(), lr=self.learning_rate)

            # Load checkpoint immediately before earliest affected slice
            if earliest_slice > 0:
                resume_slice = earliest_slice - 1
                print(f"    Resuming from checkpoint: shard_{shard_id}_slice_{resume_slice}.pt")
                self.checkpoint_manager.load_slice_checkpoint(
                    shard_id=shard_id,
                    slice_id=resume_slice,
                    model=model,
                    optimizer=optimizer,
                )
            else:
                print(f"    Earliest slice is 0: restarting shard {shard_id} from base pretrained checkpoint.")

            # Clear old checkpoints from earliest_slice onwards
            self.checkpoint_manager.clear_checkpoints_after(shard_id, earliest_slice)
            slices_trained[shard_id] = []

            # Retrain slices from earliest_slice to num_slices - 1
            for slice_id in range(earliest_slice, self.num_slices):
                slice_records = partitioned[shard_id][slice_id]
                steps, loss = self._train_single_slice(model, optimizer, slice_records)
                total_steps += steps
                slices_trained[shard_id].append(slice_id)

                # Save new checkpoint for unlearned slice
                self.checkpoint_manager.save_slice_checkpoint(
                    shard_id=shard_id,
                    slice_id=slice_id,
                    model=model,
                    optimizer=optimizer,
                    step=total_steps,
                    manifest_hash=manifest_hash,
                )
                print(f"    Retrained Shard {shard_id} Slice {slice_id}: {steps} steps, loss={loss:.4f} [checkpoint updated]")

            del model
            del optimizer
            import gc
            gc.collect()

        wall_time = time.perf_counter() - start_time
        res_stats = check_resources()

        result = SISATrainingResult(
            run_type="selective_unlearning",
            wall_time_seconds=wall_time,
            total_steps=total_steps,
            shards_trained=list(affected_map.keys()),
            slices_trained=slices_trained,
            peak_rss_gb=res_stats["rss_gb"],
            manifest_hash=manifest_hash,
        )
        print(f"[SISA Selective Unlearning] Completed in {wall_time:.2f}s, steps={total_steps}, peak RSS={res_stats['rss_gb']} GB\n")
        return result
