import numpy as np


def exponential_decay(hours_since_click, decay_rate):
    """
    Calculate recency weight using exponential decay.

    weight = exp(-lambda * time_difference)
    """

    return np.exp(
        -decay_rate * hours_since_click
    )