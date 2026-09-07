
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events
from src.models.content_representation import NewsContentModel
from src.baselines.content_based import ContentBasedBaseline
from src.personalization.history_profile import EventDynamicProfileBuilder
from src.models.dynamic_recommender import DynamicRecommender
from src.evaluation.interest_shift_evaluator import (
    evaluate_shift_events,
    summarize_results,
)


DATA_DIR = PROJECT_ROOT / "data" / "raw" / "MINDsmall_train"

SHIFT_EVENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "interest_shift_events.csv"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "interest_shift_results.csv"
)


def main():

    print()
    print("=" * 10 + " INTEREST-SHIFT ADAPTATION EXPERIMENT " + "=" * 10)
    print()

    # ---------------------------------------------------------
    # Load MIND-small
    # ---------------------------------------------------------

    print("Loading MIND-small...")

    news, behaviors = load_mind(
        str(DATA_DIR)
    )

    print(f"News: {len(news)}")
    print(f"Behaviors: {len(behaviors)}")
    print()

    # ---------------------------------------------------------
    # Create evaluation events
    # ---------------------------------------------------------

    print("Creating evaluation events...")

    evaluation_events = create_evaluation_events(
        behaviors
    )

    print(
        f"Evaluation events: {len(evaluation_events)}"
    )
    print()

    # ---------------------------------------------------------
    # Load detected interest shifts
    # ---------------------------------------------------------

    print("Loading detected interest shifts...")

    shift_events = pd.read_csv(
        SHIFT_EVENTS_PATH
    )

    shift_events["reference_time"] = pd.to_datetime(
        shift_events["reference_time"]
    )

    print(
        f"Total detected shift events: {len(shift_events)}"
    )

    # ---------------------------------------------------------
    # Select 2,000 events
    # ---------------------------------------------------------

    shift_events = (
        shift_events
        .sample(
            n=min(2000, len(shift_events)),
            random_state=42,
        )
        .sort_values("reference_time")
        .reset_index(drop=True)
    )

    print(
        f"Shift events selected for evaluation: "
        f"{len(shift_events)}"
    )

    print(
        "Unique users in selected events: "
        f"{shift_events['user_id'].nunique()}"
    )

    print()

    # ---------------------------------------------------------
    # Prepare content model
    # ---------------------------------------------------------

    print("Preparing TF-IDF content model...")

    content_model = NewsContentModel(
        max_features=20000,
        min_df=2,
        max_df=0.95,
    )

    content_model.fit(news)

    print(
        f"TF-IDF dimensions: "
        f"{content_model.get_dimension()}"
    )

    print()

    # ---------------------------------------------------------
    # Static content-based model
    # ---------------------------------------------------------

    print("Preparing static content-based model...")

    static_model = ContentBasedBaseline(
        content_model
    )

    print("Static model ready.")
    print()

    # ---------------------------------------------------------
    # Dynamic profile model
    # ---------------------------------------------------------

    print("Preparing dynamic profile model...")

    dynamic_profile_builder = (
        EventDynamicProfileBuilder(
            content_model=content_model,
            alpha=0.5,
            short_term_window_hours=24,
            decay_rate=0.05,
        )
    )

    dynamic_recommender = DynamicRecommender(
        content_model
    )

    print("Dynamic model ready.")
    print()

    # ---------------------------------------------------------
    # Run evaluation
    # ---------------------------------------------------------

    print("Starting leakage-free evaluation...")
    print()

    results = evaluate_shift_events(
        shift_events=shift_events,
        evaluation_events=evaluation_events,
        static_model=static_model,
        dynamic_profile_builder=dynamic_profile_builder,
        dynamic_recommender=dynamic_recommender,
    )

    # ---------------------------------------------------------
    # Save event-level results
    # ---------------------------------------------------------

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        RESULTS_PATH,
        index=False,
    )

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------

    summary = summarize_results(
        results
    )

    print()
    print("=" * 60)
    print("INTEREST-SHIFT RESULTS")
    print("=" * 60)
    print()

    print(summary.to_string(index=False))

    print()
    print(
        f"Event-level results saved to:"
        f"\n{RESULTS_PATH}"
    )

    print()
    print("=" * 60)
    print("EXPERIMENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
