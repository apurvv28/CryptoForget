import sys
from pathlib import Path
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.user_history import build_user_histories
from src.models.content_representation import NewsContentModel
from src.personalization.long_term import LongTermUserProfile


DATA_DIR = "data/raw/MINDsmall_train"


# --------------------------------------------------
# Load MIND
# --------------------------------------------------

news, behaviors = load_mind(DATA_DIR)


# --------------------------------------------------
# Build news content representation
# --------------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# --------------------------------------------------
# Build user histories
# --------------------------------------------------

user_histories = build_user_histories(behaviors)


print("\n========== USER HISTORIES ==========")

print("Users with history:", len(user_histories))

sample_user = next(iter(user_histories))

print("Sample user:", sample_user)
print("Number of historical clicks:",
      len(user_histories[sample_user]))

print("First 5 clicked news:",
      user_histories[sample_user][:5])


# --------------------------------------------------
# Build long-term profiles
# --------------------------------------------------

profile_model = LongTermUserProfile(content_model)

profiles = profile_model.build_profiles(user_histories)


print("\n========== LONG-TERM PROFILES ==========")

print("Users with profiles:", len(profiles))

sample_profile = profiles[sample_user]

print("Sample user:", sample_user)
print("Profile shape:", sample_profile.shape)
print("Non-zero values:", np.count_nonzero(sample_profile))