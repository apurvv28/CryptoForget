import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.user_history import build_user_histories
from src.data.preprocessing import create_interactions

from src.models.content_representation import NewsContentModel

from src.personalization.long_term import LongTermUserProfile
from src.personalization.short_term import ShortTermUserProfile
from src.personalization.fusion import DynamicUserProfile


DATA_DIR = "data/raw/MINDsmall_train"


# --------------------------------------------------
# Load data
# --------------------------------------------------

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(
    behaviors
)


# --------------------------------------------------
# Content representation
# --------------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# --------------------------------------------------
# Long-term profile
# --------------------------------------------------

user_histories = build_user_histories(
    behaviors
)

long_term_model = LongTermUserProfile(
    content_model
)

long_term_profiles = (
    long_term_model.build_profiles(
        user_histories
    )
)


# --------------------------------------------------
# Short-term profile
# --------------------------------------------------

sample_user = "U13740"

user_clicks = interactions[
    interactions["user_id"] == sample_user
].copy()

reference_time = user_clicks["time"].max()

short_term_model = ShortTermUserProfile(
    content_model,
    window_hours=24,
    decay_rate=0.05,
)

short_term_profile = (
    short_term_model.build_profile(
        user_clicks,
        reference_time,
    )
)


# --------------------------------------------------
# Dynamic profile
# --------------------------------------------------

long_term_profile = long_term_profiles[
    sample_user
]

dynamic_model = DynamicUserProfile(
    alpha=0.5
)

dynamic_profile = dynamic_model.combine(
    long_term_profile,
    short_term_profile,
)


# --------------------------------------------------
# Results
# --------------------------------------------------

print("\n========== DYNAMIC PROFILE ==========")

print("User:", sample_user)

print("Alpha:", dynamic_model.alpha)

print(
    "Long-term shape:",
    long_term_profile.shape,
)

print(
    "Short-term shape:",
    short_term_profile.shape,
)

print(
    "Dynamic shape:",
    dynamic_profile.shape,
)

print(
    "Dynamic non-zero values:",
    dynamic_profile.nnz,
)
