import pandas as pd
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.preprocessing import create_interactions


DATA_DIR = "data/raw/MINDsmall_train"



news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(behaviors)


# --------------------------------------------------
# Keep only clicks
# --------------------------------------------------

clicks = interactions[
    interactions["clicked"] == 1
].copy()

clicks = clicks.sort_values(
    ["user_id", "time"]
)


# --------------------------------------------------
# Calculate time between consecutive clicks
# --------------------------------------------------

clicks["previous_click"] = (
    clicks.groupby("user_id")["time"].shift(1)
)

clicks["time_since_previous_click"] = (
    clicks["time"] - clicks["previous_click"]
)


# Remove first click of every user
click_gaps = clicks[
    clicks["time_since_previous_click"].notna()
].copy()


print("\n========== CLICK BEHAVIOR ==========")

print("Total clicks:", len(clicks))

print(
    "Users with clicks:",
    clicks["user_id"].nunique()
)


print("\n========== TIME BETWEEN CLICKS ==========")

print(
    click_gaps["time_since_previous_click"]
    .describe()
)


# --------------------------------------------------
# Convert gaps to hours
# --------------------------------------------------

click_gaps["hours_between_clicks"] = (
    click_gaps["time_since_previous_click"]
    .dt.total_seconds()
    / 3600
)


print("\n========== HOURS BETWEEN CLICKS ==========")

print(
    click_gaps["hours_between_clicks"]
    .describe(
        percentiles=[
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
        ]
    )
)


# --------------------------------------------------
# Recent-window coverage
# --------------------------------------------------

windows = [
    6,
    12,
    24,
    48,
]


print("\n========== RECENT WINDOW ANALYSIS ==========")

for hours in windows:

    threshold = pd.Timedelta(
        hours=hours
    )

    recent_clicks = click_gaps[
        click_gaps["time_since_previous_click"]
        <= threshold
    ]

    percentage = (
        len(recent_clicks)
        / len(click_gaps)
        * 100
    )

    print(
        f"{hours:>2} hours: "
        f"{len(recent_clicks):,} clicks "
        f"({percentage:.2f}%)"
    )


# --------------------------------------------------
# Number of clicks available in recent windows
# --------------------------------------------------

print("\n========== CLICKS PER USER ==========")

latest_click = (
    clicks.groupby("user_id")["time"]
    .max()
)

for hours in windows:

    recent_counts = []

    for user_id, user_clicks in clicks.groupby(
        "user_id"
    ):

        latest_time = latest_click[user_id]

        cutoff = (
            latest_time
            - pd.Timedelta(hours=hours)
        )

        count = (
            user_clicks["time"] >= cutoff
        ).sum()

        recent_counts.append(count)

    recent_counts = pd.Series(
        recent_counts
    )

    print(
        f"{hours:>2} hours: "
        f"mean={recent_counts.mean():.2f}, "
        f"median={recent_counts.median():.0f}, "
        f"users_with_click={(recent_counts > 0).mean() * 100:.2f}%"
    )