import pandas as pd


def temporal_split(interactions):
    """
    Split interactions chronologically into train, validation and test sets.

    The split is based on time so that future interactions
    never become part of the user's historical representation.
    """

    interactions = interactions.sort_values("time").reset_index(drop=True)

    min_time = interactions["time"].min()
    max_time = interactions["time"].max()

    total_duration = max_time - min_time

    train_end = min_time + total_duration * 0.70
    validation_end = min_time + total_duration * 0.85

    train = interactions[
        interactions["time"] <= train_end
    ].copy()

    validation = interactions[
        (interactions["time"] > train_end)
        & (interactions["time"] <= validation_end)
    ].copy()

    test = interactions[
        interactions["time"] > validation_end
    ].copy()

    return train, validation, test