from scipy.sparse import csr_matrix


class DynamicUserProfile:

    def __init__(self, alpha=0.5):

        if not 0.0 <= alpha <= 1.0:
            raise ValueError("alpha must be between 0 and 1")

        self.alpha = alpha

    def combine(
        self,
        long_term_profile,
        short_term_profile,
    ):
        """
        Combine long-term and short-term user profiles.

        Both profiles are sparse TF-IDF vectors.
        """

        if long_term_profile is None:
            return short_term_profile

        if short_term_profile is None:
            return long_term_profile

        # Ensure both profiles are CSR matrices.
        long_term_profile = csr_matrix(
            long_term_profile,
            dtype=float,
        )

        short_term_profile = csr_matrix(
            short_term_profile,
            dtype=float,
        )

        dynamic_profile = (
            self.alpha * long_term_profile
            + (1.0 - self.alpha) * short_term_profile
        )

        return dynamic_profile