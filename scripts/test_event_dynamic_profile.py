import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.preprocessing import create_interactions

from src.models.content_representation import NewsContentModel

from src.personalization.history_profile import (
    EventDynamicProfileBuilder,
)


DATA_DIR = "data/raw/MINDsmall_train"


# ------------------------------------------
# 1. Load data
# ------------------------------------------

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(
    behaviors
)


# ------------------------------------------
# 2. Content representation
# ------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# ------------------------------------------
# 3. Select an actual MIND event
# ------------------------------------------

event = behaviors.iloc[1000]

user_id = event["user_id"]
reference_time = event["time"]
history = event["history"]


# ------------------------------------------
# 4. Get timestamped interactions
#    for this user BEFORE the event
# ------------------------------------------

user_interactions = interactions[
    (interactions["user_id"] == user_id)
    & (interactions["time"] < reference_time)
].copy()


# ------------------------------------------
# 5. Build dynamic profile
# ------------------------------------------

profile_builder = EventDynamicProfileBuilder(
    content_model=content_model,
    alpha=0.5,
    short_term_window_hours=24,
    decay_rate=0.05,
)


dynamic_profile = profile_builder.build_profile(
    history=history,
    timestamped_interactions=user_interactions,
    reference_time=reference_time,
)


# ------------------------------------------
# 6. Test
# ------------------------------------------

print("\n========== EVENT DYNAMIC PROFILE ==========")

print("User:", user_id)

print("Reference time:", reference_time)

print(
    "History articles:",
    len(history.split()) if history else 0,
)

print(
    "Timestamped interactions before event:",
    len(user_interactions),
)

print(
    "Timestamped clicks before event:",
    int(
        (user_interactions["clicked"] == 1).sum()
    ),
)

if dynamic_profile is None:

    print("Dynamic profile: None")

else:

    print(
        "Dynamic profile shape:",
        dynamic_profile.shape,
    )

    print(
        "Dynamic non-zero values:",
        dynamic_profile.nnz,
    )

    print(
        "Profile successfully created:",
        True,
    )