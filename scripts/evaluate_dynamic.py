import pandas as pd
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
import pandas as pd

from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events

from src.models.content_representation import NewsContentModel
from src.models.dynamic_recommender import DynamicRecommender

from src.personalization.history_profile import EventDynamicProfileBuilder
from src.evaluation.chronological import ChronologicalEvaluator

from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


DATA_DIR = "data/raw/MINDsmall_train"


def main():

    print("========== DYNAMIC RECOMMENDER EVALUATION ==========")

    # --------------------------------------------------
    # 1. Load MIND
    # --------------------------------------------------

    print("\nLoading MIND-small...")

    news, behaviors = load_mind(DATA_DIR)

    print("News:", len(news))
    print("Behaviors:", len(behaviors))

    # --------------------------------------------------
    # 2. Create evaluation events
    # --------------------------------------------------

    print("\nCreating evaluation events...")

    events = create_evaluation_events(behaviors)

    print("Evaluation events:", len(events))

    # --------------------------------------------------
    # 3. Build content representation
    # --------------------------------------------------

    print("\nTraining TF-IDF content representation...")

    content_model = NewsContentModel(
        max_features=20000
    )

    content_model.fit(news)

    print(
        "Content vector dimension:",
        content_model.get_dimension()
    )

    # --------------------------------------------------
    # 4. Create dynamic profile builder
    # --------------------------------------------------

    profile_builder = EventDynamicProfileBuilder(
        content_model=content_model,
        alpha=0.5,
        short_term_window_hours=24,
        decay_rate=0.05,
    )

    # --------------------------------------------------
    # 5. Create recommender
    # --------------------------------------------------

    recommender = DynamicRecommender(
        content_model=content_model
    )

    # --------------------------------------------------
    # 6. Create chronological evaluator
    # --------------------------------------------------

    evaluator = ChronologicalEvaluator(
        profile_builder=profile_builder,
        recommender=recommender,
    )

    # --------------------------------------------------
    # 7. Evaluate events
    # --------------------------------------------------

    auc_values = []
    mrr_values = []
    ndcg5_values = []
    ndcg10_values = []
    recall5_values = []
    recall10_values = []

    total_events = len(events)

    for index, (_, event) in enumerate(events.iterrows()):

        result = evaluator.process_event(event)

        ranked_news = result["ranked_news"]
        labels = result["labels"]

        auc = auc_score(
            ranked_news,
            labels
        )

        mrr = mrr_score(
            ranked_news,
            labels
        )

        ndcg5 = ndcg_score(
            ranked_news,
            labels,
            k=5
        )

        ndcg10 = ndcg_score(
            ranked_news,
            labels,
            k=10
        )

        recall5 = recall_score(
            ranked_news,
            labels,
            k=5
        )

        recall10 = recall_score(
            ranked_news,
            labels,
            k=10
        )

        if auc is not None:
            auc_values.append(auc)

        mrr_values.append(mrr)
        ndcg5_values.append(ndcg5)
        ndcg10_values.append(ndcg10)
        recall5_values.append(recall5)
        recall10_values.append(recall10)

        # Progress every 10,000 events
        if (index + 1) % 10000 == 0:
            print(
                f"Processed {index + 1}/{total_events} events"
            )

    # --------------------------------------------------
    # 8. Final results
    # --------------------------------------------------

    print("\n========== FINAL RESULTS ==========")

    print(
        f"AUC:       {sum(auc_values) / len(auc_values):.4f}"
    )

    print(
        f"MRR:       {sum(mrr_values) / len(mrr_values):.4f}"
    )

    print(
        f"NDCG@5:    {sum(ndcg5_values) / len(ndcg5_values):.4f}"
    )

    print(
        f"NDCG@10:   {sum(ndcg10_values) / len(ndcg10_values):.4f}"
    )

    print(
        f"Recall@5:  {sum(recall5_values) / len(recall5_values):.4f}"
    )

    print(
        f"Recall@10: {sum(recall10_values) / len(recall10_values):.4f}"
    )

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()