import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.preprocessing import create_interactions

from src.models.content_representation import NewsContentModel

from src.personalization.dynamic_profile import (
    DynamicProfileBuilder,
)


DATA_DIR = "data/raw/MINDsmall_train"

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(behaviors)

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


sample_user = "U13740"

user_interactions = interactions[
    interactions["user_id"] == sample_user
].copy()

reference_time = user_interactions["time"].max()


profile_builder = DynamicProfileBuilder(
    content_model=content_model,
    alpha=0.5,
    short_term_window_hours=24,
    decay_rate=0.05,
)


dynamic_profile = profile_builder.build_profile(
    interactions=interactions,
    user_id=sample_user,
    reference_time=reference_time,
)


print("\n========== DYNAMIC PROFILE BUILDER ==========")

print("User:", sample_user)

print("Reference time:", reference_time)

print("Alpha:", profile_builder.fusion_model.alpha)

print(
    "Short-term window:",
    profile_builder.short_term_model.window_hours,
    "hours",
)

print(
    "Dynamic profile shape:",
    dynamic_profile.shape,
)

print(
    "Dynamic non-zero values:",
    dynamic_profile.nnz,
)