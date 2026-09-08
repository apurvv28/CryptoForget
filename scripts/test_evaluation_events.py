import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.evaluation_events import (
    create_evaluation_events,
)


DATA_DIR = "data/raw/MINDsmall_train"


news, behaviors = load_mind(DATA_DIR)

events = create_evaluation_events(
    behaviors
)


print("\n========== EVALUATION EVENTS ==========")

print("Total events:", len(events))

print(
    "First event user:",
    events.iloc[0]["user_id"],
)

print(
    "First event time:",
    events.iloc[0]["time"],
)

print(
    "First event history:",
    events.iloc[0]["history"],
)

print(
    "Number of candidates:",
    len(events.iloc[0]["impressions"]),
)

print("\nCandidates:")

for impression in events.iloc[0]["impressions"]:
    print(
        impression["news_id"],
        "→",
        impression["clicked"],
    )