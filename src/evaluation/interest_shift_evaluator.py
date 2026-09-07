import pandas as pd
import numpy as np

from sklearn.metrics.pairwise import cosine_similarity

from src.evaluation.metrics import (
    auc_score,
    mrr_score,
    ndcg_score,
    recall_score,
)


def build_previous_clicks(
    evaluation_events,
    user_id,
    reference_time,
):
    """
    Reconstruct only clicks observed before
    the current recommendation event.
    """

    previous_events = evaluation_events[
        (evaluation_events["user_id"] == user_id)
        & (evaluation_events["time"] < reference_time)
    ]

    timestamped_clicks = []

    for _, previous_event in previous_events.iterrows():

        for impression in previous_event["impressions"]:

            if impression["clicked"] == 1:

                timestamped_clicks.append({
                    "user_id": user_id,
                    "time": previous_event["time"],
                    "news_id": impression["news_id"],
                    "clicked": 1,
                })

    if timestamped_clicks:

        return pd.DataFrame(
            timestamped_clicks
        )

    return pd.DataFrame(
        columns=[
            "user_id",
            "time",
            "news_id",
            "clicked",
        ]
    )


def evaluate_shift_events(
    shift_events,
    evaluation_events,
    static_model,
    dynamic_profile_builder,
    dynamic_recommender,
):
    """
    Evaluate Static and Dynamic models at
    detected interest-shift events.

    Both models use only information available
    before the recommendation event.
    """

    results = []

    evaluation_events = (
        evaluation_events
        .sort_values("time")
        .reset_index(drop=True)
    )

    shift_events = (
        shift_events
        .sort_values("reference_time")
        .reset_index(drop=True)
    )

    # Create exact lookup for detected shift events.
    shift_lookup = set()

    for _, shift in shift_events.iterrows():

        shift_lookup.add(
            (
                shift["user_id"],
                shift["reference_time"],
            )
        )

    # Process recommendation events chronologically.
    for _, event in evaluation_events.iterrows():

        user_id = event["user_id"]
        event_time = event["time"]

        # Only evaluate detected shift events.
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
        # Historical articles
        # -----------------------------------------------------

        if event["history"]:

            historical_news_ids = (
                event["history"].split()
            )

        else:

            historical_news_ids = []

        # =====================================================
        # STATIC CONTENT-BASED MODEL
        # =====================================================

        static_profile = (
            static_model._build_profile(
                historical_news_ids
            )
        )

        if static_profile is None:

            static_ranked = [
                (news_id, 0.0)
                for news_id in candidate_news
            ]

        else:

            static_ranked = []

            for news_id in candidate_news:

                news_vector = (
                    static_model
                    .content_model
                    .get_vector(news_id)
                )

                if news_vector is None:

                    score = 0.0

                else:

                    score = cosine_similarity(
                        static_profile,
                        news_vector,
                    )[0][0]

                    score = float(score)

                static_ranked.append(
                    (news_id, score)
                )

            static_ranked.sort(
                key=lambda x: x[1],
                reverse=True,
            )

        # Static metrics
        static_auc = auc_score(
            static_ranked,
            labels,
        )

        static_mrr = mrr_score(
            static_ranked,
            labels,
        )

        static_ndcg5 = ndcg_score(
            static_ranked,
            labels,
            k=5,
        )

        static_ndcg10 = ndcg_score(
            static_ranked,
            labels,
            k=10,
        )

        static_recall5 = recall_score(
            static_ranked,
            labels,
            k=5,
        )

        static_recall10 = recall_score(
            static_ranked,
            labels,
            k=10,
        )

        # =====================================================
        # DYNAMIC MODEL
        # =====================================================

        dynamic_profile = (
            dynamic_profile_builder.build_profile(
                history=event["history"],
                timestamped_interactions=(
                    timestamped_interactions
                ),
                reference_time=event_time,
            )
        )

        dynamic_ranked = (
            dynamic_recommender.rank(
                dynamic_profile=dynamic_profile,
                news_ids=candidate_news,
            )
        )

        # Dynamic metrics
        dynamic_auc = auc_score(
            dynamic_ranked,
            labels,
        )

        dynamic_mrr = mrr_score(
            dynamic_ranked,
            labels,
        )

        dynamic_ndcg5 = ndcg_score(
            dynamic_ranked,
            labels,
            k=5,
        )

        dynamic_ndcg10 = ndcg_score(
            dynamic_ranked,
            labels,
            k=10,
        )

        dynamic_recall5 = recall_score(
            dynamic_ranked,
            labels,
            k=5,
        )

        dynamic_recall10 = recall_score(
            dynamic_ranked,
            labels,
            k=10,
        )

        # =====================================================
        # STORE RESULT
        # =====================================================

        results.append({

            "user_id": user_id,
            "time": event_time,

            "static_auc": static_auc,
            "static_mrr": static_mrr,
            "static_ndcg5": static_ndcg5,
            "static_ndcg10": static_ndcg10,
            "static_recall5": static_recall5,
            "static_recall10": static_recall10,

            "dynamic_auc": dynamic_auc,
            "dynamic_mrr": dynamic_mrr,
            "dynamic_ndcg5": dynamic_ndcg5,
            "dynamic_ndcg10": dynamic_ndcg10,
            "dynamic_recall5": dynamic_recall5,
            "dynamic_recall10": dynamic_recall10,
        })

        if len(results) % 500 == 0:

            print(
                f"Evaluated {len(results)} "
                f"interest-shift events"
            )

    return pd.DataFrame(results)


def summarize_results(results):
    """
    Calculate average performance for
    Static and Dynamic models.
    """

    if results.empty:

        return pd.DataFrame()

    metrics = [
        "auc",
        "mrr",
        "ndcg5",
        "ndcg10",
        "recall5",
        "recall10",
    ]

    rows = []

    for model in [
        "static",
        "dynamic",
    ]:

        row = {
            "model": model
        }

        for metric in metrics:

            column = (
                f"{model}_{metric}"
            )

            values = (
                results[column]
                .dropna()
            )

            if len(values) > 0:

                row[metric] = values.mean()

            else:

                row[metric] = np.nan

        rows.append(row)

    return pd.DataFrame(rows)