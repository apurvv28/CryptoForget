import numpy as np
from sklearn.metrics.pairwise import cosine_similarity


class EmbeddingBasedBaseline:

    def __init__(self, embedding_model):
        self.embedding_model = embedding_model
        self.user_profiles = {}

    def fit(self, interactions):
        """
        Build a static user profile from the
        embeddings of historically clicked articles.
        """

        clicked = interactions[
            interactions["clicked"] == 1
        ]

        user_clicks = (
            clicked.groupby("user_id")["news_id"]
            .apply(list)
            .to_dict()
        )

        for user_id, news_ids in user_clicks.items():

            vectors = []

            for news_id in news_ids:

                vector = (
                    self.embedding_model
                    .get_vector(news_id)
                )

                if vector is not None:
                    vectors.append(vector)

            if vectors:

                profile = np.mean(
                    vectors,
                    axis=0
                )

                self.user_profiles[
                    user_id
                ] = profile

        return self

    def score(self, user_id, news_id):

        user_profile = (
            self.user_profiles.get(user_id)
        )

        if user_profile is None:
            return 0.0

        news_vector = (
            self.embedding_model
            .get_vector(news_id)
        )

        if news_vector is None:
            return 0.0

        score = cosine_similarity(
            user_profile.reshape(1, -1),
            news_vector.reshape(1, -1)
        )[0][0]

        return float(score)

    def rank(self, user_id, news_ids):

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