
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RESULTS_DIR = (
    PROJECT_ROOT / "results"
)

FIGURES_DIR = (
    RESULTS_DIR / "figures"
)

FIGURES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


def save_model_comparison():
    """
    Generate overall model comparison figure.
    """

    data = {
        "Model": [
            "Popularity",
            "Collaborative Filtering",
            "Static Content-Based",
            "Embedding-Based",
            "Dynamic Long+Short",
        ],
        "AUC": [
            0.6033,
            0.9303,
            0.9913,
            0.5000,
            0.5847,
        ],
        "MRR": [
            0.3448,
            0.7950,
            0.9335,
            0.2545,
            0.3226,
        ],
        "NDCG@5": [
            0.3218,
            0.7735,
            0.9447,
            0.2359,
            0.3046,
        ],
        "NDCG@10": [
            0.3725,
            0.7975,
            0.9491,
            0.2926,
            0.3613,
        ],
        "Recall@5": [
            0.4383,
            0.8407,
            0.9859,
            0.3531,
            0.4317,
        ],
        "Recall@10": [
            0.5842,
            0.9077,
            0.9983,
            0.5181,
            0.5949,
        ],
    }

    df = pd.DataFrame(data)

    df.to_csv(
        RESULTS_DIR / "model_comparison.csv",
        index=False,
    )

    metrics = [
        "AUC",
        "MRR",
        "NDCG@5",
        "NDCG@10",
        "Recall@5",
        "Recall@10",
    ]

    for metric in metrics:

        plt.figure(figsize=(10, 6))

        plt.bar(
            df["Model"],
            df[metric],
        )

        plt.ylabel(metric)
        plt.title(
            f"Overall Model Comparison — {metric}"
        )

        plt.xticks(
            rotation=25,
            ha="right",
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR
            / f"overall_{metric.lower().replace('@', '_')}.png",
            dpi=300,
        )

        plt.close()


def save_interest_shift_comparison():
    """
    Generate Static vs Dynamic comparison
    at detected interest-shift events.
    """

    path = (
        RESULTS_DIR
        / "interest_shift_results.csv"
    )

    df = pd.read_csv(path)

    summary = pd.DataFrame({
        "Model": [
            "Static Content-Based",
            "Dynamic Long+Short",
        ],
        "AUC": [
            df["static_auc"].mean(),
            df["dynamic_auc"].mean(),
        ],
        "MRR": [
            df["static_mrr"].mean(),
            df["dynamic_mrr"].mean(),
        ],
        "NDCG@5": [
            df["static_ndcg5"].mean(),
            df["dynamic_ndcg5"].mean(),
        ],
        "NDCG@10": [
            df["static_ndcg10"].mean(),
            df["dynamic_ndcg10"].mean(),
        ],
        "Recall@5": [
            df["static_recall5"].mean(),
            df["dynamic_recall5"].mean(),
        ],
        "Recall@10": [
            df["static_recall10"].mean(),
            df["dynamic_recall10"].mean(),
        ],
    })

    summary.to_csv(
        RESULTS_DIR
        / "interest_shift_summary.csv",
        index=False,
    )

    metrics = [
        "AUC",
        "MRR",
        "NDCG@5",
        "NDCG@10",
        "Recall@5",
        "Recall@10",
    ]

    for metric in metrics:

        plt.figure(figsize=(8, 6))

        plt.bar(
            summary["Model"],
            summary[metric],
        )

        plt.ylabel(metric)

        plt.title(
            f"Interest-Shift Evaluation — {metric}"
        )

        plt.xticks(
            rotation=15,
            ha="right",
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR
            / f"interest_shift_{metric.lower().replace('@', '_')}.png",
            dpi=300,
        )

        plt.close()


def save_alpha_sensitivity():
    """
    Generate alpha sensitivity plots.
    """

    path = (
        RESULTS_DIR
        / "alpha_sensitivity_results.csv"
    )

    df = pd.read_csv(path)

    metrics = [
        "auc",
        "mrr",
        "ndcg5",
        "ndcg10",
        "recall5",
        "recall10",
    ]

    for metric in metrics:

        plt.figure(figsize=(8, 6))

        plt.plot(
            df["alpha"],
            df[metric],
            marker="o",
        )

        plt.xlabel(
            "Alpha (Long-Term Weight)"
        )

        plt.ylabel(
            metric.upper()
        )

        plt.title(
            f"Alpha Sensitivity — {metric.upper()}"
        )

        plt.xticks(
            [
                0.00,
                0.25,
                0.50,
                0.75,
                1.00,
            ]
        )

        plt.grid(
            True,
            alpha=0.3,
        )

        plt.tight_layout()

        plt.savefig(
            FIGURES_DIR
            / f"alpha_{metric}.png",
            dpi=300,
        )

        plt.close()


def save_alpha_summary():
    """
    Save a clean alpha summary table.
    """

    path = (
        RESULTS_DIR
        / "alpha_sensitivity_results.csv"
    )

    df = pd.read_csv(path)

    summary = df[
        [
            "alpha",
            "auc",
            "mrr",
            "ndcg5",
            "ndcg10",
            "recall5",
            "recall10",
        ]
    ].copy()

    summary.columns = [
        "Alpha",
        "AUC",
        "MRR",
        "NDCG@5",
        "NDCG@10",
        "Recall@5",
        "Recall@10",
    ]

    summary.to_csv(
        RESULTS_DIR
        / "alpha_summary.csv",
        index=False,
    )


def main():

    print()
    print("=" * 60)
    print("GENERATING FINAL RESULTS")
    print("=" * 60)
    print()

    print(
        "1. Generating overall model comparison..."
    )

    save_model_comparison()

    print("   Done.")

    print(
        "2. Generating interest-shift comparison..."
    )

    save_interest_shift_comparison()

    print("   Done.")

    print(
        "3. Generating alpha sensitivity plots..."
    )

    save_alpha_sensitivity()

    print("   Done.")

    print(
        "4. Saving alpha summary..."
    )

    save_alpha_summary()

    print("   Done.")

    print()
    print("=" * 60)
    print("RESULT GENERATION COMPLETE")
    print("=" * 60)
    print()
    print(
        f"Figures saved to:\n{FIGURES_DIR}"
    )


if __name__ == "__main__":
    main()

