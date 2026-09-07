import numpy as np


class NewsEmbeddingModel:

    def __init__(self):
        self.embeddings = {}
        self.dimension = 0

    def fit(self, embedding_path):
        """
        Load pre-trained MIND news/entity embeddings.
        """

        with open(
            embedding_path,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                parts = line.strip().split()

                if len(parts) <= 2:
                    continue

                entity_id = parts[0]

                vector = np.asarray(
                    parts[1:],
                    dtype=np.float32
                )

                self.embeddings[
                    entity_id
                ] = vector

                self.dimension = len(vector)

        return self

    def get_vector(self, news_id):
        return self.embeddings.get(news_id)

    def get_dimension(self):
        return self.dimension