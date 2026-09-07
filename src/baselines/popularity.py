from collections import Counter


class PopularityBaseline:

    def __init__(self):
        self.popularity = Counter()

    def fit(self, interactions):
        """
        Count how many times each news article was clicked.
        """

        clicked = interactions[
            interactions["clicked"] == 1
        ]

        self.popularity = Counter(
            clicked["news_id"]
        )

        return self

    def score(self, news_id):
        return self.popularity.get(
            news_id,
            0
        )

    def rank(self, news_ids):
        """
        Rank candidate news articles by
        global click popularity.
        """

        ranked_news = [
            (
                news_id,
                self.score(news_id)
            )
            for news_id in news_ids
        ]

        ranked_news.sort(
            key=lambda x: x[1],
            reverse=True
        )

        return ranked_news