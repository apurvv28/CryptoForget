import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from src.data.loader import load_mind
from src.data.user_history import build_user_histories
from src.models.content_representation import NewsContentModel
from src.personalization.long_term import LongTermUserProfile
from src.models.content_recommender import ContentRecommender


DATA_DIR = "data/raw/MINDsmall_train"


# --------------------------------------------------
# Load data
# --------------------------------------------------

news, behaviors = load_mind(DATA_DIR)


# --------------------------------------------------
# Build news representations
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


# --------------------------------------------------
# Build long-term user profiles
# --------------------------------------------------

profile_model = LongTermUserProfile(content_model)

user_profiles = profile_model.build_profiles(
    user_histories
)


# --------------------------------------------------
# Create recommender
# --------------------------------------------------

recommender = ContentRecommender(
    content_model,
    user_profiles
)


# --------------------------------------------------
# Test recommendation
# --------------------------------------------------

sample_user = "U13740"

candidate_news = [
    "N55528",
    "N19639",
    "N61837",
    "N53526",
    "N38324",
]


ranked_news = recommender.rank(
    sample_user,
    candidate_news
)


print("\n========== RECOMMENDATIONS ==========")

print("User:", sample_user)

for rank, (news_id, score) in enumerate(
    ranked_news,
    start=1
):
    print(
        f"{rank}. {news_id} | "
        f"score = {score:.4f}"
    )