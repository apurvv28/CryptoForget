"""
Phase 3: Baseline Training Benchmark Harness.

Per Docs 01 (§7), 03 (§5), 04 (§7), and 08 (§2):
1. Builds versioned dataset manifests with SHA-256 digests.
2. Trains M0 (Original Model) on complete dataset across random seeds.
3. Trains M1 (Clean Full Retraining Reference) on retained dataset after deletion.
4. Generates standardized Run Manifests (environment, commit, loss, perplexity).
5. Syncs artifacts and manifests to AWS S3.
"""

import json
from pathlib import Path
import time
from typing import Any

from ml.data.dataset_builder import DatasetBuilder
from ml.data.partitioner import Record
from ml.evaluation.utility_metrics import evaluate_model_loss_and_ppl
from ml.scripts.run_experiment import generate_sample_conversations
from ml.training.baseline_trainer import BaselineTrainer
from transformers import AutoTokenizer


def run_baseline_benchmark(seeds: list[int] = [42, 123]) -> dict[str, Any]:
    print("=" * 70)
    print("PHASE 3: BASELINE TRAINING HARNESS (M0 & M1 BENCHMARK)")
    print("=" * 70)

    # 1. Dataset Generation
    all_records, deleted_ids, test_texts = generate_sample_conversations()
    retained_records = [r for r in all_records if r.record_id not in deleted_ids]
    deleted_texts = [r.text for r in all_records if r.record_id in deleted_ids]

    # 2. Dataset Manifest Creation
    builder = DatasetBuilder(output_dir="./data/processed", seed=42)
    manifest_m0, path_m0 = builder.build_manifest(
        records=all_records,
        dataset_version="v1.0-full",
        sync_to_s3=True,
    )
    manifest_m1, path_m1 = builder.build_manifest(
        records=retained_records,
        dataset_version="v1.0-retained",
        sync_to_s3=True,
    )

    print(f"\n[Dataset Manifests]")
    print(f" -> Full M0 Manifest Hash     : {manifest_m0.manifest_hash[:16]}... ({len(all_records)} records)")
    print(f" -> Retained M1 Manifest Hash : {manifest_m1.manifest_hash[:16]}... ({len(retained_records)} records)")

    tokenizer = AutoTokenizer.from_pretrained("./models/distilgpt2")
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    results_m0 = []
    results_m1 = []

    # 3. Multi-seed training loop
    for seed in seeds:
        print(f"\n>>> Running Experiment Seed: {seed} <<<")
        trainer = BaselineTrainer(
            model_path="./models/distilgpt2",
            output_dir="./data/checkpoints/baseline",
            learning_rate=5e-5,
            epochs=1,
            seed=seed,
        )

        # Train M0: Original
        model_m0, res_m0 = trainer.train(
            records=all_records,
            run_name="M0_original",
            dataset_version=manifest_m0.dataset_version,
            dataset_manifest_hash=manifest_m0.manifest_hash,
            sync_to_s3=True,
        )
        test_eval_m0 = evaluate_model_loss_and_ppl(model_m0, test_texts, tokenizer)
        del_eval_m0 = evaluate_model_loss_and_ppl(model_m0, deleted_texts, tokenizer)

        results_m0.append({
            "seed": seed,
            "wall_time": res_m0.wall_time_seconds,
            "steps": res_m0.total_steps,
            "train_loss": res_m0.final_loss,
            "train_ppl": res_m0.perplexity,
            "test_loss": test_eval_m0["loss"],
            "test_ppl": test_eval_m0["perplexity"],
            "target_loss": del_eval_m0["loss"],
            "target_ppl": del_eval_m0["perplexity"],
            "artifact_hash": res_m0.run_manifest.artifact_hash,
        })

        # Train M1: Clean Full Retrain Reference
        model_m1, res_m1 = trainer.train(
            records=retained_records,
            run_name="M1_clean_reference",
            dataset_version=manifest_m1.dataset_version,
            dataset_manifest_hash=manifest_m1.manifest_hash,
            sync_to_s3=True,
        )
        test_eval_m1 = evaluate_model_loss_and_ppl(model_m1, test_texts, tokenizer)
        del_eval_m1 = evaluate_model_loss_and_ppl(model_m1, deleted_texts, tokenizer)

        results_m1.append({
            "seed": seed,
            "wall_time": res_m1.wall_time_seconds,
            "steps": res_m1.total_steps,
            "train_loss": res_m1.final_loss,
            "train_ppl": res_m1.perplexity,
            "test_loss": test_eval_m1["loss"],
            "test_ppl": test_eval_m1["perplexity"],
            "target_loss": del_eval_m1["loss"],
            "target_ppl": del_eval_m1["perplexity"],
            "artifact_hash": res_m1.run_manifest.artifact_hash,
        })

    # Summary JSON
    summary = {
        "timestamp": time.time(),
        "model": "distilgpt2-82M",
        "seeds": seeds,
        "m0_original": results_m0,
        "m1_clean_reference": results_m1,
    }

    summary_file = Path("./data/results/phase3_baseline_benchmark.json")
    summary_file.write_text(json.dumps(summary, indent=2))

    # Optional S3 upload of the benchmark summary
    try:
        from app.services.s3_service import s3_service
        s3_service.upload_file(summary_file, f"benchmarks/{summary_file.name}")
        print(f"[Benchmark] Synced benchmark summary to S3.")
    except Exception as e:
        print(f"[Benchmark] S3 upload skipped/failed: {e}")

    # Print Report Table
    print("\n" + "=" * 70)
    print("PHASE 3 REPRODUCIBLE BASELINE REPORT (Doc 08 Tables A & C)")
    print("=" * 70)
    print(f"{'Condition':<22} | {'Seed':<5} | {'Time (s)':<8} | {'Test Loss':<9} | {'Target Loss':<11} | {'Model Hash'}")
    print("-" * 75)
    for r in results_m0:
        print(f"{'M0 (Original)':<22} | {r['seed']:<5} | {r['wall_time']:<8.2f} | {r['test_loss']:<9.4f} | {r['target_loss']:<11.4f} | {r['artifact_hash'][:12]}...")
    print("-" * 75)
    for r in results_m1:
        print(f"{'M1 (Clean Retrain)':<22} | {r['seed']:<5} | {r['wall_time']:<8.2f} | {r['test_loss']:<9.4f} | {r['target_loss']:<11.4f} | {r['artifact_hash'][:12]}...")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_baseline_benchmark()
