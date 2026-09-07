import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.data.loader import load_mind
from src.data.evaluation_events import (
    create_evaluation_events,
)
from src.data.preprocessing import create_interactions

from src.models.content_representation import NewsContentModel
from src.models.dynamic_recommender import DynamicRecommender

from src.personalization.history_profile import (
    EventDynamicProfileBuilder,
)

from src.evaluation.chronological import (
    ChronologicalEvaluator,
)


DATA_DIR = "data/raw/MINDsmall_train"


# ------------------------------------------
# 1. Load data
# ------------------------------------------

news, behaviors = load_mind(DATA_DIR)

events = create_evaluation_events(
    behaviors
)

interactions = create_interactions(
    behaviors
)


# ------------------------------------------
# 2. Content model
# ------------------------------------------

content_model = NewsContentModel(
    max_features=20000,
    min_df=2,
    max_df=0.95,
)

content_model.fit(news)


# ------------------------------------------
# 3. Dynamic profile
# ------------------------------------------

profile_builder = EventDynamicProfileBuilder(
    content_model=content_model,
    alpha=0.5,
    short_term_window_hours=24,
    decay_rate=0.05,
)


# ------------------------------------------
# 4. Recommender
# ------------------------------------------

recommender = DynamicRecommender(
    content_model=content_model
)


# ------------------------------------------
# 5. Chronological evaluator
# ------------------------------------------

evaluator = ChronologicalEvaluator(
    profile_builder=profile_builder,
    recommender=recommender,
)


# ------------------------------------------
# 6. Process first 10 events
# ------------------------------------------

test_events = events.head(10)

print("\n========== CHRONOLOGICAL TEST ==========")

for index, event in test_events.iterrows():

    result = evaluator.process_event(
        event
    )

    print(
        f"\nEvent {index + 1}"
    )

    print(
        "User:",
        result["user_id"]
    )

    print(
        "Time:",
        result["time"]
    )

    print(
        "Candidates:",
        len(result["ranked_news"])
    )

    clicked_news = [
        news_id
        for news_id, label
        in result["labels"].items()
        if label == 1
    ]

    print(
        "Actual clicks:",
        clicked_news
    )

    if result["dynamic_profile"] is not None:

        print(
            "Profile:",
            result["dynamic_profile"].shape
        )

    else:

        print(
            "Profile: None"
        )


print(
    "Tracked users:",
    len(evaluator.user_click_store.clicks)
)

print(
    "Total stored clicks:",
    sum(
        len(clicks)
        for clicks in evaluator.user_click_store.clicks.values()
    )
)