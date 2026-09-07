
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events
from src.models.content_representation import NewsContentModel
from src.personalization.history_profile import EventDynamicProfileBuilder
from src.models.dynamic_recommender import DynamicRecommender
from src.evaluation.interest_shift_evaluator import (
    build_previous_clicks,
)
from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


DATA_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "MINDsmall_train"
)

SHIFT_EVENTS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "interest_shift_events.csv"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "results"
    / "alpha_sensitivity_results.csv"
)


def evaluate_alpha(
    alpha,
    shift_events,
    evaluation_events,
    profile_builder,
    recommender,
):
    """
    Evaluate one alpha value at detected
    interest-shift events.

    Only information available before each
    recommendation event is used.
    """

    results = []

    evaluation_events = (
        evaluation_events
        .sort_values("time")
        .reset_index(drop=True)
    )

    shift_lookup = set()

    for _, shift in shift_events.iterrows():

        shift_lookup.add(
            (
                shift["user_id"],
                shift["reference_time"],
            )
        )

    for _, event in evaluation_events.iterrows():

        user_id = event["user_id"]
        event_time = event["time"]

        if (
            user_id,
            event_time,
        ) not in shift_lookup:

            continue

        # -----------------------------------------------------
        # Candidates and labels
        # -----------------------------------------------------

        candidate_news = []
        labels = {}

        for impression in event["impressions"]:

            news_id = impression["news_id"]
            clicked = impression["clicked"]

            candidate_news.append(news_id)
            labels[news_id] = clicked

        # -----------------------------------------------------
        # Previous observed clicks
        # -----------------------------------------------------

        timestamped_interactions = (
            build_previous_clicks(
                evaluation_events,
                user_id,
                event_time,
            )
        )

        # -----------------------------------------------------
        # Build dynamic profile
        # -----------------------------------------------------

        dynamic_profile = (
            profile_builder.build_profile(
                history=event["history"],
                timestamped_interactions=(
                    timestamped_interactions
                ),
                reference_time=event_time,
            )
        )

        # -----------------------------------------------------
        # Rank candidates
        # -----------------------------------------------------

        ranked_news = recommender.rank(
            dynamic_profile=dynamic_profile,
            news_ids=candidate_news,
        )

        # -----------------------------------------------------
        # Metrics
        # -----------------------------------------------------

        auc = auc_score(
            ranked_news,
            labels,
        )

        mrr = mrr_score(
            ranked_news,
            labels,
        )

        ndcg5 = ndcg_score(
            ranked_news,
            labels,
            k=5,
        )

        ndcg10 = ndcg_score(
            ranked_news,
            labels,
            k=10,
        )

        recall5 = recall_score(
            ranked_news,
            labels,
            k=5,
        )

        recall10 = recall_score(
            ranked_news,
            labels,
            k=10,
        )

        results.append({

            "alpha": alpha,

            "user_id": user_id,

            "time": event_time,

            "auc": auc,

            "mrr": mrr,

            "ndcg5": ndcg5,

            "ndcg10": ndcg10,

            "recall5": recall5,

            "recall10": recall10,
        })

        if len(results) % 500 == 0:

            print(
                f"Alpha {alpha:.2f}: "
                f"evaluated {len(results)} "
                f"events"
            )

    return pd.DataFrame(results)


def main():

    print()
    print("=" * 60)
    print("ALPHA SENSITIVITY EXPERIMENT")
    print("=" * 60)
    print()

    # ---------------------------------------------------------
    # Load MIND-small
    # ---------------------------------------------------------

    print("Loading MIND-small...")

    news, behaviors = load_mind(
        str(DATA_DIR)
    )

    print(
        f"News: {len(news)}"
    )

    print(
        f"Behaviors: {len(behaviors)}"
    )

    print()

    # ---------------------------------------------------------
    # Create evaluation events
    # ---------------------------------------------------------

    print(
        "Creating evaluation events..."
    )

    evaluation_events = (
        create_evaluation_events(
            behaviors
        )
    )

    print(
        f"Evaluation events: "
        f"{len(evaluation_events)}"
    )

    print()

    # ---------------------------------------------------------
    # Load interest-shift events
    # ---------------------------------------------------------

    print(
        "Loading detected interest shifts..."
    )

    shift_events = pd.read_csv(
        SHIFT_EVENTS_PATH
    )

    shift_events["reference_time"] = (
        pd.to_datetime(
            shift_events["reference_time"]
        )
    )

    print(
        f"Total detected shift events: "
        f"{len(shift_events)}"
    )

    # Use exactly the same sample as the
    # previous interest-shift experiment.

    shift_events = (
        shift_events
        .sample(
            n=min(
                2000,
                len(shift_events),
            ),
            random_state=42,
        )
        .sort_values(
            "reference_time"
        )
        .reset_index(
            drop=True
        )
    )

    print(
        f"Shift events selected: "
        f"{len(shift_events)}"
    )

    print(
        f"Unique users: "
        f"{shift_events['user_id'].nunique()}"
    )

    print()

    # ---------------------------------------------------------
    # Prepare TF-IDF model
    # ---------------------------------------------------------

    print(
        "Preparing TF-IDF content model..."
    )

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
    # Dynamic recommender
    # ---------------------------------------------------------

    recommender = DynamicRecommender(
        content_model
    )

    # ---------------------------------------------------------
    # Alpha values
    # ---------------------------------------------------------

    alpha_values = [
        0.00,
        0.25,
        0.50,
        0.75,
        1.00,
    ]

    all_results = []

    # ---------------------------------------------------------
    # Evaluate every alpha
    # ---------------------------------------------------------

    for alpha in alpha_values:

        print()
        print("-" * 60)
        print(
            f"Evaluating alpha = {alpha:.2f}"
        )
        print("-" * 60)
        print()

        profile_builder = (
            EventDynamicProfileBuilder(
                content_model=content_model,
                alpha=alpha,
                short_term_window_hours=24,
                decay_rate=0.05,
            )
        )

        alpha_results = evaluate_alpha(
            alpha=alpha,
            shift_events=shift_events,
            evaluation_events=evaluation_events,
            profile_builder=profile_builder,
            recommender=recommender,
        )

        all_results.append(
            alpha_results
        )

        print()
        print(
            f"Alpha {alpha:.2f} completed."
        )

    # ---------------------------------------------------------
    # Combine results
    # ---------------------------------------------------------

    final_results = pd.concat(
        all_results,
        ignore_index=True,
    )

    # ---------------------------------------------------------
    # Save event-level results
    # ---------------------------------------------------------

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    final_results.to_csv(
        RESULTS_PATH,
        index=False,
    )

    # ---------------------------------------------------------
    # Calculate summary
    # ---------------------------------------------------------

    summary = (
        final_results
        .groupby("alpha")[
            [
                "auc",
                "mrr",
                "ndcg5",
                "ndcg10",
                "recall5",
                "recall10",
            ]
        ]
        .mean()
        .reset_index()
    )

    # ---------------------------------------------------------
    # Display summary
    # ---------------------------------------------------------

    print()
    print("=" * 60)
    print("ALPHA SENSITIVITY RESULTS")
    print("=" * 60)
    print()

    print(
        summary.to_string(
            index=False
        )
    )

    print()
    print(
        f"Results saved to:"
        f"\n{RESULTS_PATH}"
    )

    print()
    print("=" * 60)
    print("ALPHA EXPERIMENT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()

