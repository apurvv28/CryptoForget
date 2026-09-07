import numpy as np
from scipy import sparse
from sklearn.metrics.pairwise import cosine_similarity


class DynamicRecommender:

    def __init__(self, content_model):
        self.content_model = content_model

    def score(self, dynamic_profile, news_id):
        if dynamic_profile is None:
            return 0.0

        news_vector = self.content_model.get_vector(news_id)

        if news_vector is None:
            return 0.0

        if sparse.issparse(dynamic_profile):
            profile = dynamic_profile
        else:
            profile = np.asarray(dynamic_profile)

        if sparse.issparse(news_vector):
            vector = news_vector
        else:
            vector = np.asarray(news_vector)

        return float(cosine_similarity(profile, vector)[0][0])

    def rank(self, dynamic_profile, news_ids):
        if dynamic_profile is None:
            return [(news_id, 0.0) for news_id in news_ids]

        valid_news_ids = []
        vectors = []

        for news_id in news_ids:
            vector = self.content_model.get_vector(news_id)

            if vector is not None:
                valid_news_ids.append(news_id)
                vectors.append(vector)

        if not vectors:
            return [(news_id, 0.0) for news_id in news_ids]

        if sparse.issparse(dynamic_profile):
            profile = dynamic_profile
        else:
            profile = np.asarray(dynamic_profile)

        if all(sparse.issparse(vector) for vector in vectors):
            candidate_matrix = sparse.vstack(vectors)
        else:
            candidate_matrix = np.vstack([
                vector.toarray().ravel()
                if sparse.issparse(vector)
                else np.asarray(vector).ravel()
                for vector in vectors
            ])

        scores = cosine_similarity(
            profile,
            candidate_matrix,
        )[0]

        scored_news = list(zip(valid_news_ids, scores))
        valid_set = set(valid_news_ids)

        scored_news.extend(
            (news_id, 0.0)
            for news_id in news_ids
            if news_id not in valid_set
        )

        scored_news.sort(key=lambda item: item[1], reverse=True)

        return [
            (news_id, float(score))
            for news_id, score in scored_news
        ]