import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.evaluation_events import create_evaluation_events
from src.models.news_embeddings import NewsEmbeddingModel
from src.baselines.embedding_based import EmbeddingBasedBaseline
from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


DATA_DIR = "data/raw/MINDsmall_train"

EMBEDDING_PATH = (
    "data/raw/MINDsmall_train/entity_embedding.vec"
)


def main():

    print(
        "========== EMBEDDING-BASED "
        "BASELINE EVALUATION =========="
    )

    # 1. Load MIND-small
    print("\nLoading MIND-small...")

    news, behaviors = load_mind(DATA_DIR)

    print("News:", len(news))
    print("Behaviors:", len(behaviors))

    # 2. Create evaluation events
    print("\nCreating evaluation events...")

    events = create_evaluation_events(
        behaviors
    )

    print(
        "Evaluation events:",
        len(events)
    )

    # 3. Create interactions
    print("\nCreating interactions...")

    interactions = []

    for _, row in behaviors.iterrows():

        for impression in row["impressions"].split():

            news_id, clicked = (
                impression.rsplit("-", 1)
            )

            interactions.append({
                "user_id": row["user_id"],
                "time": row["time"],
                "news_id": news_id,
                "clicked": int(clicked),
            })

    interactions = pd.DataFrame(
        interactions
    )

    print(
        "Interactions:",
        len(interactions)
    )

    # 4. Load MIND embeddings
    print(
        "\nLoading MIND entity embeddings..."
    )

    embedding_model = NewsEmbeddingModel()

    embedding_model.fit(
        EMBEDDING_PATH
    )

    print(
        "Embedding dimension:",
        embedding_model.get_dimension()
    )

    print(
        "Embeddings loaded:",
        len(embedding_model.embeddings)
    )

    # 5. Train embedding-based baseline
    print(
        "\nTraining embedding-based baseline..."
    )

    model = EmbeddingBasedBaseline(
        embedding_model
    )

    model.fit(
        interactions
    )

    print(
        "Embedding-based baseline trained."
    )

    # 6. Evaluation metrics
    auc_values = []
    mrr_values = []
    ndcg5_values = []
    ndcg10_values = []
    recall5_values = []
    recall10_values = []

    total_events = len(events)

    # 7. Evaluate events
    for index, (_, event) in enumerate(
        events.iterrows()
    ):

        user_id = event["user_id"]

        candidate_news = []
        labels = {}

        for impression in event["impressions"]:

            news_id = impression["news_id"]
            clicked = impression["clicked"]

            candidate_news.append(news_id)
            labels[news_id] = clicked

        ranked_news = model.rank(
            user_id,
            candidate_news
        )

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
                f"Processed "
                f"{index + 1}/{total_events} events"
            )

    # 8. Final results
    print(
        "\n========== FINAL RESULTS =========="
    )

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