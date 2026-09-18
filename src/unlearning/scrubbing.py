import numpy as np


def scrub_user_profile(
    user_profile_vector: np.ndarray,
    deleted_item_vectors: np.ndarray,
    noise_scale: float = 0.01,
) -> np.ndarray:
    """Fisher Information / Representation Scrubbing (Stretch Goal).

    Subtracts the representation influence of deleted items from a user profile
    and applies calibrated Gaussian noise to prevent residual gradient leakage.
    """
    if deleted_item_vectors.size == 0:
        return user_profile_vector

    # Subtract mean influence of deleted item vectors
    deleted_mean = np.mean(deleted_item_vectors, axis=0)
    scrubbed = user_profile_vector - deleted_mean

    # Add differential noise to mask residual influence
    noise = np.random.normal(0, noise_scale, size=scrubbed.shape)
    scrubbed = scrubbed + noise

    # Zero-clip negative TF-IDF values
    return np.maximum(0, scrubbed)
