import pandas as pd
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
import pandas as pd

from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events

from src.baselines.collaborative_filtering import (
    CollaborativeFilteringBaseline
)

from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


DATA_DIR = "data/raw/MINDsmall_train"


def main():

    print(
        "========== COLLABORATIVE FILTERING "
        "BASELINE EVALUATION =========="
    )

    # 1. Load MIND-small
    print("\nLoading MIND-small...")
    news, behaviors = load_mind(DATA_DIR)

    print("News:", len(news))
    print("Behaviors:", len(behaviors))

    # 2. Create evaluation events
    print("\nCreating evaluation events...")
    events = create_evaluation_events(behaviors)

    print("Evaluation events:", len(events))

    # 3. Create interactions
    print("\nCreating interactions...")

    interactions = []

    for _, row in behaviors.iterrows():

        for impression in row["impressions"].split():

            news_id, clicked = impression.rsplit("-", 1)

            interactions.append({
                "user_id": row["user_id"],
                "time": row["time"],
                "news_id": news_id,
                "clicked": int(clicked),
            })

    interactions = pd.DataFrame(interactions)

    # 4. Train collaborative filtering
    print("\nTraining collaborative filtering baseline...")

    cf_model = CollaborativeFilteringBaseline()
    cf_model.fit(interactions)

    print("Collaborative filtering baseline trained.")

    # 5. Evaluation metrics
    auc_values = []
    mrr_values = []
    ndcg5_values = []
    ndcg10_values = []
    recall5_values = []
    recall10_values = []

    total_events = len(events)

    # 6. Evaluate events
    for index, (_, event) in enumerate(events.iterrows()):

        user_id = event["user_id"]

        candidate_news = []
        labels = {}

        for impression in event["impressions"]:

            news_id = impression["news_id"]
            clicked = impression["clicked"]

            candidate_news.append(news_id)
            labels[news_id] = clicked

        # Rank candidates for this user
        ranked_news = cf_model.rank(
            user_id,
            candidate_news
        )

        # Calculate metrics
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

        if (index + 1) % 10000 == 0:
            print(
                f"Processed {index + 1}/{total_events} events"
            )

    # 7. Final results
    print("\n========== FINAL RESULTS ==========")

    print(
        f"AUC:       "
        f"{sum(auc_values) / len(auc_values):.4f}"
    )

    print(
        f"MRR:       "
        f"{sum(mrr_values) / len(mrr_values):.4f}"
    )

    print(
        f"NDCG@5:    "
        f"{sum(ndcg5_values) / len(ndcg5_values):.4f}"
    )

    print(
        f"NDCG@10:   "
        f"{sum(ndcg10_values) / len(ndcg10_values):.4f}"
    )

    print(
        f"Recall@5:  "
        f"{sum(recall5_values) / len(recall5_values):.4f}"
    )

    print(
        f"Recall@10: "
        f"{sum(recall10_values) / len(recall10_values):.4f}"
    )

    print("\nEvaluation complete.")


if __name__ == "__main__":
    main()