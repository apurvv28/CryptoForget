from collections import defaultdict


def build_user_histories(behaviors):
    """
    Build historical clicked-news lists for each user
    from the MIND history column.
    """

    user_histories = defaultdict(list)

    for _, row in behaviors.iterrows():

        history = row["history"]

        if not history:
            continue

        news_ids = history.split()

        user_histories[row["user_id"]].extend(news_ids)

    return dict(user_histories)
