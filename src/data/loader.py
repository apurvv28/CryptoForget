import pandas as pd
from pathlib import Path


NEWS_COLUMNS = [
    "news_id",
    "category",
    "subcategory",
    "title",
    "abstract",
    "url",
    "title_entities",
    "abstract_entities",
]

BEHAVIOR_COLUMNS = [
    "impression_id",
    "user_id",
    "time",
    "history",
    "impressions",
]


def load_news(data_dir: str) -> pd.DataFrame:
    """
    Load the MIND news metadata.
    """
    path = Path(data_dir) / "news.tsv"

    news = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=NEWS_COLUMNS,
        quoting=3,
        keep_default_na=False,
    )

    return news


def load_behaviors(data_dir: str) -> pd.DataFrame:
    """
    Load the MIND user behavior data.
    """
    path = Path(data_dir) / "behaviors.tsv"

    behaviors = pd.read_csv(
        path,
        sep="\t",
        header=None,
        names=BEHAVIOR_COLUMNS,
        quoting=3,
        keep_default_na=False,
    )

    behaviors["time"] = pd.to_datetime(
        behaviors["time"],
        errors="coerce",
    )

    return behaviors


def load_mind(data_dir: str):
    """
    Load both MIND news and behavior data.
    """
    news = load_news(data_dir)
    behaviors = load_behaviors(data_dir)

    return news, behaviors