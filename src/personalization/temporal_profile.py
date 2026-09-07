import pandas as pd


def get_user_history_before_time(
    interactions,
    user_id,
    reference_time,
):

    user_history = interactions[
        (interactions["user_id"] == user_id)
        & (interactions["clicked"] == 1)
        & (interactions["time"] < reference_time)
    ].copy()

    user_history = user_history.sort_values("time")

    return user_history