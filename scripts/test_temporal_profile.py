import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.preprocessing import create_interactions
from src.personalization.temporal_profile import get_user_history_before_time


DATA_DIR = "data/raw/MINDsmall_train"

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(behaviors)

sample_user = "U13740"

user_interactions = interactions[
    interactions["user_id"] == sample_user
].copy()

reference_time = user_interactions["time"].max()

history = get_user_history_before_time(
    interactions,
    sample_user,
    reference_time,
)

print("\n========== TEMPORAL PROFILE TEST ==========")
print("User:", sample_user)
print("Reference time:", reference_time)
print("Total user interactions:", len(user_interactions))
print("Historical clicks before reference:", len(history))

if not history.empty:
    print("First historical click:", history["time"].min())
    print("Last historical click:", history["time"].max())
    print(
        "Any leakage:",
        bool((history["time"] >= reference_time).any())
    )
else:
    print("No historical clicks found.")