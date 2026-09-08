import pandas as pd

from src.personalization.long_term import LongTermUserProfile
from src.personalization.short_term import ShortTermUserProfile
from src.personalization.fusion import DynamicUserProfile
from src.personalization.temporal_profile import get_user_history_before_time


class DynamicProfileBuilder:
    def __init__(
        self,
        content_model,
        alpha=0.5,
        short_term_window_hours=24,
        decay_rate=0.05,
    ):
        self.content_model = content_model

        self.long_term_model = LongTermUserProfile(
            content_model
        )

        self.short_term_model = ShortTermUserProfile(
            content_model,
            window_hours=short_term_window_hours,
            decay_rate=decay_rate,
        )

        self.fusion_model = DynamicUserProfile(
            alpha=alpha
        )

    def build_profile(
        self,
        interactions,
        user_id,
        reference_time,
    ):
        """
        Build a user's dynamic profile using ONLY
        interactions that occurred before reference_time.
        """

        historical_clicks = get_user_history_before_time(
            interactions,
            user_id,
            reference_time,
        )

        if historical_clicks.empty:
            return None

        clicked_news_ids = historical_clicks["news_id"].tolist()

        long_term_profile = (
            self.long_term_model.build_profile(
                clicked_news_ids
            )
        )

        short_term_profile = (
            self.short_term_model.build_profile(
                historical_clicks,
                reference_time,
            )
        )

        dynamic_profile = self.fusion_model.combine(
            long_term_profile,
            short_term_profile,
        )

        return dynamic_profile