import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class ContentRecommender:
    """
    Static content-aware recommendation model.

    Uses a user's long-term preference profile
    to score candidate news articles.
    """

    def __init__(self, content_model, user_profiles):
        self.content_model = content_model
        self.user_profiles = user_profiles

    def score(self, user_id, news_id):
        """
        Calculate relevance score between a user
        and a single news article.
        """

        user_profile = self.user_profiles.get(user_id)

        if user_profile is None:
            return 0.0

        news_vector = self.content_model.get_vector(news_id)

        if news_vector is None:
            return 0.0

        score = cosine_similarity(
            user_profile,
            news_vector
        )[0][0]

        return float(score)

    def rank(self, user_id, news_ids):
        """
        Rank candidate news articles for a user.
        """

        scored_news = []

        for news_id in news_ids:

            score = self.score(user_id, news_id)

            scored_news.append(
                (news_id, score)
            )

        scored_news.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return scored_news