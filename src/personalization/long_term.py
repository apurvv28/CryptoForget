import numpy as np


class LongTermUserProfile:
    """
    Builds a user's long-term preference representation
    from historically clicked news articles.
    """

    def __init__(self, news_content_model):
        self.news_content_model = news_content_model

    def build_profile(self, clicked_news_ids):
        """
        Create one user's long-term preference vector.
        """

        indices = []

        for news_id in clicked_news_ids:
            index = self.news_content_model.news_id_to_index.get(news_id)

            if index is not None:
                indices.append(index)

        if not indices:
            return None

        # Select all news vectors at once
        vectors = self.news_content_model.news_vectors[indices]

        # Average the vectors
        profile = np.asarray(vectors.mean(axis=0))

        return profile

    def build_profiles(self, user_histories):
        """
        Build long-term profiles for all users.
        """

        profiles = {}

        for user_id, clicked_news_ids in user_histories.items():

            profile = self.build_profile(clicked_news_ids)

            if profile is not None:
                profiles[user_id] = profile

        return profiles