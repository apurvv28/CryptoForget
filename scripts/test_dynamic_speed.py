import pandas as pd
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import time

from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events

from src.models.content_representation import NewsContentModel
from src.models.dynamic_recommender import DynamicRecommender

from src.personalization.history_profile import EventDynamicProfileBuilder
from src.evaluation.chronological import ChronologicalEvaluator


DATA_DIR = "data/raw/MINDsmall_train"
N_EVENTS = 1000


def main():

    print("========== DYNAMIC SPEED TEST ==========")

    # Load data
    news, behaviors = load_mind(DATA_DIR)

    print("Creating events...")

    events = create_evaluation_events(behaviors)

    events = events.head(N_EVENTS)

    print("Events:", len(events))

    # Content model
    print("Training TF-IDF...")

    content_model = NewsContentModel(
        max_features=20000
    )

    content_model.fit(news)

    # Dynamic profile
    profile_builder = EventDynamicProfileBuilder(
        content_model=content_model,
        alpha=0.5,
        short_term_window_hours=24,
        decay_rate=0.05,
    )

    # Recommender
    recommender = DynamicRecommender(
        content_model=content_model
    )

    # Evaluator
    evaluator = ChronologicalEvaluator(
        profile_builder=profile_builder,
        recommender=recommender,
    )

    # Measure only evaluation time
    start = time.perf_counter()

    for _, event in events.iterrows():
        evaluator.process_event(event)

    end = time.perf_counter()

    elapsed = end - start

    print()
    print("========== SPEED RESULT ==========")
    print(f"Events processed: {N_EVENTS}")
    print(f"Time taken: {elapsed:.2f} seconds")
    print(f"Events / second: {N_EVENTS / elapsed:.2f}")

    estimated_seconds = (
        156965 / (N_EVENTS / elapsed)
    )

    print(
        f"Estimated full evaluation: "
        f"{estimated_seconds / 60:.2f} minutes"
    )


if __name__ == "__main__":
    main()