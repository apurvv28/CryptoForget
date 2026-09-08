from collections import defaultdict


class UserClickStore:

    def __init__(self):
        self.clicks = defaultdict(list)

    def add_click(
        self,
        user_id,
        news_id,
        timestamp,
    ):
        """
        Store a newly observed click.
        """

        self.clicks[user_id].append({
            "user_id": user_id,
            "news_id": news_id,
            "time": timestamp,
            "clicked": 1,
        })

    def get_clicks(self, user_id):
        """
        Return all clicks observed so far for a user.
        """

        return self.clicks[user_id]

    def get_click_count(self, user_id):
        return len(self.clicks[user_id])