import pandas as pd


def create_evaluation_events(behaviors):
    """
    Convert MIND behavior rows into recommendation events.

    Each event contains:
        - user_id
        - time
        - history
        - candidate news IDs
        - click labels
    """

    events = []

    for _, row in behaviors.iterrows():

        if not row["impressions"]:
            continue

        impressions = []

        for impression in row["impressions"].split():

            news_id, clicked = impression.rsplit("-", 1)

            impressions.append({
                "news_id": news_id,
                "clicked": int(clicked),
            })

        events.append({
            "impression_id": row["impression_id"],
            "user_id": row["user_id"],
            "time": row["time"],
            "history": row["history"],
            "impressions": impressions,
        })

    events = pd.DataFrame(events)

    events = events.sort_values(
        "time"
    ).reset_index(drop=True)

    return events