from sklearn.feature_extraction.text import TfidfVectorizer


class NewsContentModel:
    """
    Creates TF-IDF representations for MIND news articles.
    """

    def __init__(
        self,
        max_features=20000,
        min_df=2,
        max_df=0.95,
    ):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            min_df=min_df,
            max_df=max_df,
            stop_words="english",
        )

        self.news_vectors = None
        self.news_id_to_index = {}

    def prepare_text(self, news):
        """
        Combine title and abstract into one text representation.
        """

        title = news["title"].fillna("")
        abstract = news["abstract"].fillna("")

        return title + " " + abstract

    def fit(self, news):
        """
        Learn the TF-IDF vocabulary from news articles.
        """

        text = self.prepare_text(news)

        self.news_vectors = self.vectorizer.fit_transform(text)

        self.news_id_to_index = {
            news_id: index
            for index, news_id in enumerate(news["news_id"])
        }

        return self

    def transform(self, news):
        """
        Transform news articles using the already learned vocabulary.
        """

        text = self.prepare_text(news)

        return self.vectorizer.transform(text)

    def get_vector(self, news_id):
        """
        Get the TF-IDF vector for a specific news article.
        """

        index = self.news_id_to_index.get(news_id)

        if index is None:
            return None

        return self.news_vectors[index]

    def get_dimension(self):
        """
        Return dimensionality of the news representation.
        """

        if self.news_vectors is None:
            return 0

        return self.news_vectors.shape[1]