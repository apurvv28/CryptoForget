import pandas as pd


def parse_history(history):
    """
    Convert a user's history string into a list of news IDs.
    """
    if not history:
        return []

    return history.split()


def parse_impressions(impressions):
    """
    Convert MIND impressions into (news_id, clicked) pairs.
    """
    if not impressions:
        return []

    result = []

    for impression in impressions.split():
        news_id, clicked = impression.rsplit("-", 1)

        result.append(
            {
                "news_id": news_id,
                "clicked": int(clicked),
            }
        )

    return result


def create_interactions(behaviors):
    """
    Convert MIND behavior records into interaction-level data.
    """

    interactions = []

    for _, row in behaviors.iterrows():

        impressions = parse_impressions(row["impressions"])

        for impression in impressions:
            interactions.append(
                {
                    "impression_id": row["impression_id"],
                    "user_id": row["user_id"],
                    "time": row["time"],
                    "news_id": impression["news_id"],
                    "clicked": impression["clicked"],
                }
            )

    interactions = pd.DataFrame(interactions)

    interactions = interactions.sort_values(
        ["time", "user_id"]
    ).reset_index(drop=True)

    return interactions