import numpy as np
from scipy.sparse import vstack

from src.personalization.recency import exponential_decay


class ShortTermUserProfile:

    def __init__(
        self,
        news_content_model,
        window_hours=24,
        decay_rate=0.05,
    ):
        self.news_content_model = news_content_model
        self.window_hours = window_hours
        self.decay_rate = decay_rate

    def build_profile(
        self,
        user_clicks,
        reference_time,
    ):
        if user_clicks.empty:
            return None

        clicks = user_clicks[
            user_clicks["clicked"] == 1
        ].copy()

        if clicks.empty:
            return None

        clicks["hours_since_click"] = (
            reference_time - clicks["time"]
        ).dt.total_seconds() / 3600

        clicks = clicks[
            (clicks["hours_since_click"] >= 0)
            & (
                clicks["hours_since_click"]
                <= self.window_hours
            )
        ]

        if clicks.empty:
            return None

        vectors = []
        weights = []

        for _, row in clicks.iterrows():

            vector = self.news_content_model.get_vector(
                row["news_id"]
            )

            if vector is None:
                continue

            weight = exponential_decay(
                row["hours_since_click"],
                self.decay_rate,
            )

            vectors.append(vector)
            weights.append(weight)

        if not vectors:
            return None

        # Stack all sparse vectors into one matrix.
        vectors = vstack(vectors)

        weights = np.asarray(
            weights,
            dtype=float,
        )

        # Weighted sum of the sparse vectors.
        weighted_profile = (
            vectors.multiply(
                weights.reshape(-1, 1)
            ).sum(axis=0)
        )

        total_weight = weights.sum()

        if total_weight == 0:
            return None

        weighted_profile = (
            weighted_profile / total_weight
        )

        return weighted_profile