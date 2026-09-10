"""
Builds the servable model artifacts for the recommendation service.

This is the "training" step. It does NOT train a classic weighted model —
the content model is a TF-IDF representation of the news corpus, plus a
lookup of each known user's long-term (historical) click list.

Anushka's retraining pipeline should re-run this script whenever the news
catalog / interaction data is refreshed, then hot-swap the two .joblib
files produced here. The FastAPI service only ever reads these files.

Usage:
    python scripts/build_content_model.py \
        --data-dir ../data/raw/MINDsmall_train \
        --output-dir models
"""

import argparse
import sys
from pathlib import Path

import joblib

# Make the project's `src` package importable regardless of cwd.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.data.loader import load_mind
from src.data.user_history import build_user_histories
from src.models.content_representation import NewsContentModel


def build(data_dir: str, output_dir: str, max_features: int = 20000) -> None:
    data_dir_path = Path(data_dir)
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)

    print(f"Loading MIND data from {data_dir_path} ...")
    news, behaviors = load_mind(str(data_dir_path))
    print(f"  news: {len(news)} rows | behaviors: {len(behaviors)} rows")

    print("Fitting TF-IDF content model on news corpus ...")
    content_model = NewsContentModel(max_features=max_features)
    content_model.fit(news)
    print(f"  content vector dimension: {content_model.get_dimension()}")

    print("Building long-term user histories (for known MIND users) ...")
    user_histories = build_user_histories(behaviors)
    print(f"  users with history: {len(user_histories)}")

    content_model_path = output_dir_path / "content_model.joblib"
    user_histories_path = output_dir_path / "user_histories.joblib"

    joblib.dump(content_model, content_model_path)
    joblib.dump(user_histories, user_histories_path)

    print(f"Saved: {content_model_path}")
    print(f"Saved: {user_histories_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-dir",
        default=str(PROJECT_ROOT / "data" / "raw" / "MINDsmall_train"),
        help="Directory containing news.tsv and behaviors.tsv",
    )
    parser.add_argument(
        "--output-dir",
        default=str(Path(__file__).resolve().parents[1] / "models"),
        help="Directory to write content_model.joblib and user_histories.joblib",
    )
    parser.add_argument("--max-features", type=int, default=20000)
    args = parser.parse_args()

    build(args.data_dir, args.output_dir, args.max_features)
