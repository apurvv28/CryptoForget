import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from src.data.loader import load_mind
from src.data.preprocessing import create_interactions
from src.data.temporal_split import temporal_split


DATA_DIR = "data/raw/MINDsmall_train"


# Load raw MIND data
news, behaviors = load_mind(DATA_DIR)


# Convert impressions into interaction-level records
interactions = create_interactions(behaviors)


# Chronological split
train, validation, test = temporal_split(interactions)


print("\n========== DATASET ==========")

print("News:", news.shape)
print("Behaviors:", behaviors.shape)
print("Interactions:", interactions.shape)


print("\n========== TIME RANGE ==========")

print("Overall:")
print(interactions["time"].min())
print(interactions["time"].max())


print("\nTrain:")
print(train["time"].min())
print(train["time"].max())
print("Rows:", len(train))


print("\nValidation:")
print(validation["time"].min())
print(validation["time"].max())
print("Rows:", len(validation))


print("\nTest:")
print(test["time"].min())
print(test["time"].max())
print("Rows:", len(test))


print("\n========== USERS ==========")

print("Train users:", train["user_id"].nunique())
print("Validation users:", validation["user_id"].nunique())
print("Test users:", test["user_id"].nunique())


print("\n========== CLICKS ==========")

print("Train clicks:", train["clicked"].sum())
print("Validation clicks:", validation["clicked"].sum())
print("Test clicks:", test["clicked"].sum())