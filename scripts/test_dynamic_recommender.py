import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.preprocessing import create_interactions

from src.models.content_representation import NewsContentModel
from src.models.dynamic_recommender import DynamicRecommender

from src.personalization.dynamic_profile import (
    DynamicProfileBuilder,
)


DATA_DIR = "data/raw/MINDsmall_train"

# --------------------------------------------------
# 1. Load data
# --------------------------------------------------

news, behaviors = load_mind(DATA_DIR)

interactions = create_interactions(behaviors)


# --------------------------------------------------
# 2. Build content representation
# --------------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# --------------------------------------------------
# 3. Build dynamic profile system
# --------------------------------------------------

profile_builder = DynamicProfileBuilder(
    content_model=content_model,
    alpha=0.5,
    short_term_window_hours=24,
    decay_rate=0.05,
)


recommender = DynamicRecommender(
    content_model=content_model,
    profile_builder=profile_builder,
)


# --------------------------------------------------
# 4. Select a real MIND behavior
# --------------------------------------------------

behavior = behaviors[
    behaviors["history"].notna()
    & behaviors["impressions"].notna()
].iloc[0]

user_id = behavior["user_id"]
reference_time = behavior["time"]


# --------------------------------------------------
# 5. Extract the actual candidate articles
# --------------------------------------------------

impressions = behavior["impressions"].split()

candidate_news = []
actual_labels = {}

for impression in impressions:
    news_id, clicked = impression.rsplit("-", 1)

    candidate_news.append(news_id)
    actual_labels[news_id] = int(clicked)


# --------------------------------------------------
# 6. Rank the actual candidates
# --------------------------------------------------

ranked_news = recommender.rank(
    interactions=interactions,
    user_id=user_id,
    news_ids=candidate_news,
    reference_time=reference_time,
)


# --------------------------------------------------
# 7. Display results
# --------------------------------------------------

print("\n========== DYNAMIC RECOMMENDER TEST ==========")

print("User:", user_id)
print("Reference time:", reference_time)

print("\nCandidate articles:", len(candidate_news))

print("\nRanked recommendations:")

for rank, (news_id, score) in enumerate(
    ranked_news,
    start=1,
):
    print(
        f"{rank:2d}. "
        f"{news_id} | "
        f"score={score:.4f} | "
        f"actual_click={actual_labels[news_id]}"
    )