import pandas as pd
import numpy as np


def get_clicked_categories(
    news,
    interactions
):
    """
    Attach news categories to clicked interactions.
    """

    category_map = (
        news[["news_id", "category"]]
        .drop_duplicates("news_id")
        .set_index("news_id")["category"]
        .to_dict()
    )

    clicked = interactions[
        interactions["clicked"] == 1
    ].copy()

    clicked["category"] = (
        clicked["news_id"]
        .map(category_map)
    )

    clicked = clicked.dropna(
        subset=["category"]
    )

    return clicked


def calculate_user_category_history(
    clicked_interactions
):
    """
    Build chronological category histories
    for every user.
    """

    user_histories = {}

    for user_id, group in (
        clicked_interactions
        .groupby("user_id")
    ):

        group = group.sort_values("time")

        user_histories[user_id] = group[
            ["time", "news_id", "category"]
        ].reset_index(drop=True)

    return user_histories


def calculate_shift_score(
    historical_categories,
    recent_categories
):
    """
    Measure how different recent interests are
    from historical interests.

    Shift score:
        0 = no change
        1 = completely different
    """

    historical_set = set(
        historical_categories
    )

    recent_set = set(
        recent_categories
    )

    if not historical_set or not recent_set:
        return 0.0

    overlap = len(
        historical_set & recent_set
    )

    union = len(
        historical_set | recent_set
    )

    if union == 0:
        return 0.0

    similarity = overlap / union

    return 1.0 - similarity


def identify_interest_shifts(
    clicked_interactions,
    recent_window_hours=24,
    minimum_history=3,
    minimum_recent=2,
    shift_threshold=0.5,
):
    """
    Identify user events where recent interests
    differ substantially from historical interests.

    A shift event requires:

    1. At least minimum_history historical clicks.
    2. At least minimum_recent recent clicks.
    3. Recent clicks within the specified time window.
    4. Shift score >= shift_threshold.
    """

    results = []

    clicked_interactions = (
        clicked_interactions
        .sort_values(
            ["user_id", "time"]
        )
        .reset_index(drop=True)
    )

    for user_id, user_data in (
        clicked_interactions
        .groupby("user_id")
    ):

        user_data = user_data.sort_values(
            "time"
        ).reset_index(drop=True)

        for index in range(
            minimum_history,
            len(user_data)
        ):

            reference_time = (
                user_data.loc[index, "time"]
            )

            historical = user_data.iloc[
                :index
            ]

            recent_start = (
                reference_time
                - pd.Timedelta(
                    hours=recent_window_hours
                )
            )

            recent = historical[
                historical["time"]
                >= recent_start
            ]

            # Need enough historical and recent behavior.
            if len(historical) < minimum_history:
                continue

            if len(recent) < minimum_recent:
                continue

            # Historical interest excluding recent window.
            older = historical[
                historical["time"]
                < recent_start
            ]

            if len(older) < minimum_history:
                continue

            historical_categories = (
                older["category"]
                .dropna()
                .tolist()
            )

            recent_categories = (
                recent["category"]
                .dropna()
                .tolist()
            )

            shift_score = calculate_shift_score(
                historical_categories,
                recent_categories,
            )

            if shift_score >= shift_threshold:

                results.append({
                    "user_id": user_id,
                    "reference_time": reference_time,
                    "historical_clicks": len(
                        older
                    ),
                    "recent_clicks": len(
                        recent
                    ),
                    "historical_categories": (
                        list(
                            set(
                                historical_categories
                            )
                        )
                    ),
                    "recent_categories": (
                        list(
                            set(
                                recent_categories
                            )
                        )
                    ),
                    "shift_score": shift_score,
                })

    return pd.DataFrame(results)


def summarize_shift_events(
    shift_events
):
    """
    Produce a compact summary of detected
    interest-shift events.
    """

    if shift_events.empty:
        return {
            "shift_events": 0,
            "users": 0,
            "mean_shift_score": 0.0,
            "median_shift_score": 0.0,
        }

    return {
        "shift_events": len(
            shift_events
        ),
        "users": shift_events[
            "user_id"
        ].nunique(),
        "mean_shift_score": (
            shift_events[
                "shift_score"
            ].mean()
        ),
        "median_shift_score": (
            shift_events[
                "shift_score"
            ].median()
        ),
    }