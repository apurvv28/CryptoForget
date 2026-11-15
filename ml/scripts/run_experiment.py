"""
CryptoForget Machine Unlearning Experiment Runner.

Executes end-to-end SISA sharding, slicing, checkpointing, and unlearning
on DistilGPT2 (82M) per Docs 01 (§7), 03 (§5), 06 (§4), and 08 (§1-§8).
Compares:
  - M0: Initial SISA trained model
  - M1: Clean Full Retraining reference (without deleted records)
  - M2: SISA Selective Unlearning
"""

import json
from pathlib import Path
import time
from typing import Any

from ml.data.partitioner import Record, SISAPartitioner
from ml.evaluation.efficiency_metrics import calculate_efficiency_metrics
from ml.evaluation.forgetting_metrics import evaluate_unlearning_effectiveness
from ml.inference.aggregator import SISAEnsemble
from ml.training.baseline_trainer import BaselineTrainer
from ml.training.sisa_trainer import SISATrainer
from transformers import AutoTokenizer


def generate_sample_conversations() -> tuple[list[Record], set[str], list[str]]:
    """
    Generates a controlled sample conversation dataset with distinct users.
    Returns:
        all_records: complete training dataset
        deleted_ids: set of record IDs belonging to a user requesting deletion
        test_texts: separate held-out evaluation texts
    """
    users = ["user_alice", "user_bob", "user_charlie", "user_david"]
    records: list[Record] = []
    rec_counter = 0

    dialogues = {
        "user_alice": [
            "Alice says: My secret personal project is building quantum solar panels in Seattle.",
            "Alice says: Don't forget my favourite encryption cipher is AES-256 with argon2id.",
            "Alice says: I regularly travel between Seattle and Vancouver for research meetings.",
        ],
        "user_bob": [
            "Bob says: The best machine learning conference for unlearning papers is IEEE S&P.",
            "Bob says: In python, always remember to set random seeds for deterministic results.",
            "Bob says: Distributed training across CPU shards requires careful gradient synchronization.",
        ],
        "user_charlie": [
            "Charlie says: Differential privacy guarantees that individual sample presence is bounded.",
            "Charlie says: Sharded models can be ensembled using output logit distributions.",
            "Charlie says: Verifiable certificates require Ed25519 digital signatures and Merkle trees.",
        ],
        "user_david": [
            "David says: Machine unlearning allows users to exercise their right to be forgotten.",
            "David says: SISA reduces retraining time by sharding datasets and saving slice checkpoints.",
            "David says: Pre-tombstoning prevents training jobs from reading deleted records.",
        ],
    }

    for user_id, lines in dialogues.items():
        for line in lines:
            rec_id = f"rec_{rec_counter:04d}"
            records.append(Record(record_id=rec_id, user_id=user_id, text=line))
            rec_counter += 1

    # Alice requests deletion of all her records
    deleted_ids = {r.record_id for r in records if r.user_id == "user_alice"}

    # Separate held-out evaluation texts
    test_texts = [
        "In artificial intelligence, privacy and machine unlearning are critical research topics.",
        "Computer systems must respect user privacy and enforce data deletion rights.",
    ]

    return records, deleted_ids, test_texts


def run_pipeline() -> dict[str, Any]:
    print("=" * 70)
    print("CRYPTOFORGET: SISA MACHINE UNLEARNING PIPELINE (DistilGPT2 - 82M)")
    print("=" * 70)

    num_shards = 2
    num_slices = 3
    model_path = "./models/distilgpt2"
    checkpoint_dir = "./data/checkpoints"
    results_dir = Path("./data/results")
    results_dir.mkdir(parents=True, exist_ok=True)

    tokenizer = AutoTokenizer.from_pretrained(model_path)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    # 1. Dataset Generation
    all_records, deleted_ids, test_texts = generate_sample_conversations()
    retained_records = [r for r in all_records if r.record_id not in deleted_ids]
    deleted_texts = [r.text for r in all_records if r.record_id in deleted_ids]

    print(f"Total records: {len(all_records)} | Retained: {len(retained_records)} | To Delete: {len(deleted_ids)}")

    # 2. Partitioner Inspection
    partitioner = SISAPartitioner(num_shards=num_shards, num_slices=num_slices, seed=42)
    lineage = partitioner.generate_lineage_index(all_records)
    affected = partitioner.find_affected_shards_and_slices(deleted_ids, lineage)
    print(f"\nLineage Analysis:")
    print(f" -> Deletion target affected shards: {affected}")

    # 3. M0: SISA Initial Training
    trainer = SISATrainer(
        model_path=model_path,
        checkpoint_dir=checkpoint_dir,
        num_shards=num_shards,
        num_slices=num_slices,
        learning_rate=5e-5,
        epochs_per_slice=1,
    )
    init_result = trainer.initial_train(all_records)

    # Load initial SISA ensemble
    initial_ensemble = SISAEnsemble(
        model_path=model_path,
        checkpoint_dir=checkpoint_dir,
        num_shards=num_shards,
        final_slice_id=num_slices - 1,
    )

    # 4. M1: Clean Full Retraining (Gold Standard)
    baseline_trainer = BaselineTrainer(
        model_path=model_path,
        output_dir="./data/checkpoints/baseline",
        learning_rate=5e-5,
        epochs=1,
    )
    clean_model, full_retrain_result = baseline_trainer.train(
        records=retained_records,
        run_name="clean_full_retrain",
    )

    # 5. M2: SISA Selective Unlearning
    unlearn_result = trainer.unlearn(all_records=all_records, deleted_record_ids=deleted_ids)

    # Load unlearned SISA ensemble
    unlearned_ensemble = SISAEnsemble(
        model_path=model_path,
        checkpoint_dir=checkpoint_dir,
        num_shards=num_shards,
        final_slice_id=num_slices - 1,
    )

    # 6. Efficiency Metrics Calculation
    eff_metrics = calculate_efficiency_metrics(
        t_init_sisa=init_result.wall_time_seconds,
        t_full_del=full_retrain_result.wall_time_seconds,
        t_sisa_del=unlearn_result.wall_time_seconds,
        steps_full=full_retrain_result.total_steps,
        steps_sisa=unlearn_result.total_steps,
    )

    # 7. Forgetting & Utility Evaluation
    eval_metrics = evaluate_unlearning_effectiveness(
        original_model=initial_ensemble,
        unlearned_model=unlearned_ensemble,
        clean_retrain_model=clean_model,
        deleted_texts=deleted_texts,
        retained_texts=test_texts,
        tokenizer=tokenizer,
    )

    # 8. Generation Demonstration
    print("\n--- Model Response Verification ---")
    prompt = "Alice says: My secret personal project is"
    print(f"Prompt: '{prompt}'")
    gen_original = initial_ensemble.generate(prompt, max_new_tokens=15)
    gen_unlearned = unlearned_ensemble.generate(prompt, max_new_tokens=15)
    print(f"Original M0 generation  : {gen_original}")
    print(f"Unlearned M2 generation : {gen_unlearned}")

    summary = {
        "efficiency": eff_metrics,
        "evaluation": eval_metrics,
        "shards": num_shards,
        "slices": num_slices,
        "timestamp": time.time(),
    }

    # Save summary
    results_path = results_dir / "unlearning_results.json"
    results_path.write_text(json.dumps(summary, indent=2))
    print(f"\nResults successfully saved to: {results_path}")

    # Print summary table
    print("\n" + "=" * 70)
    print("RESEARCH METRIC SUMMARY (Doc 08 Tables A & C)")
    print("=" * 70)
    print(f"{'Metric':<35} | {'Value'}")
    print("-" * 55)
    print(f"{'Clean Full Retrain Time':<35} | {eff_metrics['t_full_del_sec']} s")
    print(f"{'SISA Unlearning Time':<35} | {eff_metrics['t_sisa_del_sec']} s")
    print(f"{'Deletion Speedup':<35} | {eff_metrics['speedup']}x")
    print(f"{'Retraining Time Saved':<35} | {eff_metrics['time_saved_pct']}%")
    print(f"{'Training Step Reduction':<35} | {eff_metrics['step_reduction_pct']}%")
    print(f"{'Break-even Request Count':<35} | {eff_metrics['break_even_requests']}")
    print("-" * 55)
    print(f"{'Deleted Targets Loss (Original)':<35} | {eval_metrics['deleted_targets']['original_loss']}")
    print(f"{'Deleted Targets Loss (Unlearned)':<35} | {eval_metrics['deleted_targets']['unlearned_loss']}")
    print(f"{'Deleted Targets Loss (Clean Retrain)':<35} | {eval_metrics['deleted_targets']['clean_reference_loss']}")
    print(f"{'KL Divergence to Clean Reference':<35} | {eval_metrics['kl_to_clean_reference']}")
    print("=" * 70)

    return summary


if __name__ == "__main__":
    run_pipeline()
