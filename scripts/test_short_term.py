import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.preprocessing import create_interactions
from src.models.content_representation import NewsContentModel
from src.personalization.short_term import ShortTermUserProfile


DATA_DIR = "data/raw/MINDsmall_train"


# --------------------------------------------------
# Load data
# --------------------------------------------------

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(
    behaviors
)


# --------------------------------------------------
# Content model
# --------------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# --------------------------------------------------
# Select one user
# --------------------------------------------------

sample_user = "U13740"

user_clicks = interactions[
    interactions["user_id"] == sample_user
].copy()


reference_time = user_clicks["time"].max()


# --------------------------------------------------
# Short-term profile
# --------------------------------------------------

short_term_model = ShortTermUserProfile(
    content_model,
    window_hours=24,
    decay_rate=0.05,
)


profile = short_term_model.build_profile(
    user_clicks,
    reference_time,
)


print("\n========== SHORT-TERM PROFILE ==========")

print("User:", sample_user)

print(
    "Reference time:",
    reference_time,
)

print(
    "Total user interactions:",
    len(user_clicks),
)

print(
    "User clicks:",
    user_clicks["clicked"].sum(),
)

print(
    "Window:",
    short_term_model.window_hours,
    "hours",
)

print(
    "Decay rate:",
    short_term_model.decay_rate,
)

if profile is not None:

    print(
        "Profile shape:",
        profile.shape,
    )

    print(
        "Non-zero values:",
        profile.nnz,
    )

else:

    print("No recent profile available.")
    