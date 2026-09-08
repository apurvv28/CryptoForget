from src.personalization.long_term import LongTermUserProfile
from src.personalization.short_term import ShortTermUserProfile
from src.personalization.fusion import DynamicUserProfile


class EventDynamicProfileBuilder:

    def __init__(
        self,
        content_model,
        alpha=0.5,
        short_term_window_hours=24,
        decay_rate=0.05,
    ):
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
        history,
        timestamped_interactions,
        reference_time,
    ):
        """
        Build a dynamic user profile for one MIND
        recommendation event.

        Long-term profile:
            MIND historical clicks.

        Short-term profile:
            Timestamped clicks occurring before the
            current recommendation event.

        No interaction at or after reference_time
        is allowed into the profile.
        """

        # ------------------------------------------
        # 1. Long-term profile
        # ------------------------------------------

        if history:
            clicked_news_ids = history.split()

            long_term_profile = (
                self.long_term_model.build_profile(
                    clicked_news_ids
                )
            )
        else:
            long_term_profile = None

        # ------------------------------------------
        # 2. Short-term profile
        # ------------------------------------------

        short_term_interactions = (
            timestamped_interactions[
                timestamped_interactions["time"]
                < reference_time
            ].copy()
        )

        short_term_profile = (
            self.short_term_model.build_profile(
                short_term_interactions,
                reference_time,
            )
        )

        # ------------------------------------------
        # 3. Combine
        # ------------------------------------------

        dynamic_profile = self.fusion_model.combine(
            long_term_profile,
            short_term_profile,
        )

        return dynamic_profile