import pandas as pd
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.preprocessing import create_interactions

from src.evaluation.interest_shift import (
    get_clicked_categories,
    identify_interest_shifts,
    summarize_shift_events,
)


DATA_DIR = "data/raw/MINDsmall_train"

OUTPUT_PATH = (
    "data/processed/interest_shift_events.csv"
)


def main():

    print(
        "========== INTEREST-SHIFT DETECTION =========="
    )

    # 1. Load MIND-small
    print("\nLoading MIND-small...")

    news, behaviors = load_mind(
        DATA_DIR
    )

    print(
        "News:",
        len(news)
    )

    print(
        "Behaviors:",
        len(behaviors)
    )

    # 2. Create interactions
    print(
        "\nCreating interactions..."
    )

    interactions = create_interactions(
        behaviors
    )

    print(
        "Interactions:",
        len(interactions)
    )

    # 3. Attach categories
    print(
        "\nMapping clicked articles "
        "to categories..."
    )

    clicked = get_clicked_categories(
        news,
        interactions
    )

    print(
        "Clicked interactions with "
        "category:",
        len(clicked)
    )

    # 4. Detect shifts
    print(
        "\nDetecting interest shifts..."
    )

    shift_events = identify_interest_shifts(
        clicked_interactions=clicked,
        recent_window_hours=24,
        minimum_history=3,
        minimum_recent=2,
        shift_threshold=0.5,
    )

    print(
        "Interest-shift events:",
        len(shift_events)
    )

    # 5. Summary
    summary = summarize_shift_events(
        shift_events
    )

    print(
        "\n========== SHIFT SUMMARY =========="
    )

    print(
        "Shift events:",
        summary["shift_events"]
    )

    print(
        "Unique users:",
        summary["users"]
    )

    print(
        "Mean shift score:",
        f"{summary['mean_shift_score']:.4f}"
    )

    print(
        "Median shift score:",
        f"{summary['median_shift_score']:.4f}"
    )

    # 6. Save
    if not shift_events.empty:

        shift_events.to_csv(
            OUTPUT_PATH,
            index=False
        )

        print(
            "\nSaved shift events to:"
        )

        print(
            OUTPUT_PATH
        )

    else:

        print(
            "\nNo interest-shift events detected."
        )


if __name__ == "__main__":
    main()