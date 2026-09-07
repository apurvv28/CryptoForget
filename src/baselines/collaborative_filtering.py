import numpy as np
from collections import defaultdict


class CollaborativeFilteringBaseline:

    def __init__(self):
        self.user_items = defaultdict(set)
        self.item_users = defaultdict(set)
        self.item_popularity = defaultdict(int)

    def fit(self, interactions):
        """
        Build user-item interaction relationships
        using clicked news articles only.
        """

        clicked = interactions[
            interactions["clicked"] == 1
        ]

        for _, row in clicked.iterrows():

            user_id = row["user_id"]
            news_id = row["news_id"]

            self.user_items[user_id].add(news_id)
            self.item_users[news_id].add(user_id)
            self.item_popularity[news_id] += 1

        return self

    def score(self, user_id, news_id):
        """
        Score a candidate news article for a user
        using user-based collaborative filtering.

        Users who interacted with the candidate article
        are compared with the target user's history.
        """

        user_history = self.user_items.get(
            user_id,
            set()
        )

        if not user_history:
            return 0.0

        candidate_users = self.item_users.get(
            news_id,
            set()
        )

        if not candidate_users:
            return 0.0

        score = 0.0

        for other_user in candidate_users:

            other_history = self.user_items.get(
                other_user,
                set()
            )

            if not other_history:
                continue

            intersection = len(
                user_history & other_history
            )

            union = len(
                user_history | other_history
            )

            if union == 0:
                continue

            similarity = intersection / np.sqrt(
                len(user_history)
                * len(other_history)
            )

            score += similarity

        return float(score)

    def rank(self, user_id, news_ids):
        """
        Rank candidate news articles for a user.
        """

        scored_news = []

        for news_id in news_ids:

            score = self.score(
                user_id,
                news_id
            )

            scored_news.append(
                (news_id, score)
            )

        scored_news.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return scored_news