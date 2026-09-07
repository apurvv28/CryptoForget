from sklearn.metrics.pairwise import cosine_similarity


class ContentBasedBaseline:

    def __init__(self, content_model):
        self.content_model = content_model
        self.user_profiles = {}

    def fit(self, interactions):
        """
        Build one static content profile per user
        from all historical clicked articles.
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

            profile = self._build_profile(news_ids)

            if profile is not None:
                self.user_profiles[user_id] = profile

        return self

    def _build_profile(self, news_ids):
        """
        Create a static user profile by averaging
        the TF-IDF vectors of clicked articles.
        """

        vectors = []

        for news_id in news_ids:

            vector = self.content_model.get_vector(
                news_id
            )

            if vector is not None:
                vectors.append(vector)

        if not vectors:
            return None

        profile = vectors[0]

        for vector in vectors[1:]:
            profile = profile + vector

        profile = profile / len(vectors)

        return profile

    def score(self, user_id, news_id):
        """
        Calculate cosine similarity between the
        user's static profile and a candidate article.
        """

        user_profile = self.user_profiles.get(
            user_id
        )

        if user_profile is None:
            return 0.0

        news_vector = self.content_model.get_vector(
            news_id
        )

        if news_vector is None:
            return 0.0

        score = cosine_similarity(
            user_profile,
            news_vector
        )[0][0]

        return float(score)

    def rank(self, user_id, news_ids):
        """
        Rank candidate articles using static
        content-based personalization.
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