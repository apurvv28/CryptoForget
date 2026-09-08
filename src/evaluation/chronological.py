import pandas as pd

from src.personalization.user_click_store import UserClickStore


class ChronologicalEvaluator:

    def __init__(
        self,
        profile_builder,
        recommender,
    ):
        self.profile_builder = profile_builder
        self.recommender = recommender

        # Stores only clicks that have already been observed.
        self.user_click_store = UserClickStore()

    def get_user_clicks_before_event(
        self,
        user_id,
    ):
        return self.user_click_store.get_clicks(user_id)

    def process_event(
        self,
        event,
    ):
        user_id = event["user_id"]
        reference_time = event["time"]

        # --------------------------------------------------
        # 1. Get previously observed clicks
        # --------------------------------------------------

        previous_clicks = (
            self.get_user_clicks_before_event(
                user_id
            )
        )

        # --------------------------------------------------
        # 2. Convert previous clicks to DataFrame
        # --------------------------------------------------

        if previous_clicks:

            timestamped_interactions = pd.DataFrame(
                previous_clicks
            )

        else:

            timestamped_interactions = pd.DataFrame(
                columns=[
                    "user_id",
                    "time",
                    "news_id",
                    "clicked",
                ]
            )

        # --------------------------------------------------
        # 3. Build dynamic profile
        # --------------------------------------------------

        dynamic_profile = (
            self.profile_builder.build_profile(
                history=event["history"],
                timestamped_interactions=(
                    timestamped_interactions
                ),
                reference_time=reference_time,
            )
        )

        # --------------------------------------------------
        # 4. Extract candidates and labels
        # --------------------------------------------------

        candidate_news = []
        actual_labels = {}

        for impression in event["impressions"]:

            news_id = impression["news_id"]
            clicked = impression["clicked"]

            candidate_news.append(news_id)
            actual_labels[news_id] = clicked

        # --------------------------------------------------
        # 5. Rank candidates
        # --------------------------------------------------

        ranked_news = self.recommender.rank(
            dynamic_profile=dynamic_profile,
            news_ids=candidate_news,
        )

        # --------------------------------------------------
        # 6. Observe clicks AFTER recommendation
        # --------------------------------------------------

        for impression in event["impressions"]:

            if impression["clicked"] == 1:

                self.user_click_store.add_click(
                    user_id=user_id,
                    news_id=impression["news_id"],
                    timestamp=reference_time,
                )

        # --------------------------------------------------
        # 7. Return evaluation result
        # --------------------------------------------------

        return {
            "user_id": user_id,
            "time": reference_time,
            "ranked_news": ranked_news,
            "labels": actual_labels,
            "dynamic_profile": dynamic_profile,
        }