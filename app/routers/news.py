from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from src.config import DATA_DIR
from src.data.loader import load_news

router = APIRouter(prefix="/api/v1/news", tags=["News Catalog"])

# Cache loaded news dataframe
_news_df_cache: Optional[pd.DataFrame] = None


def get_cached_news_df() -> pd.DataFrame:
    global _news_df_cache
    if _news_df_cache is None:
        try:
            _news_df_cache = load_news(str(DATA_DIR))
        except Exception:
            _news_df_cache = pd.DataFrame(columns=["news_id", "category", "subcategory", "title", "abstract", "url"])
    return _news_df_cache


@router.get("", response_model=Dict[str, Any])
def list_news(
    category: Optional[str] = Query(None, description="Filter by category (e.g. news, sports, finance)"),
    search: Optional[str] = Query(None, description="Search in title or abstract"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    """Returns paginated news articles from the MIND dataset."""
    df = get_cached_news_df()

    if df.empty:
        return {"total": 0, "articles": []}

    filtered = df
    if category and category.lower() != "all":
        filtered = filtered[filtered["category"].str.lower() == category.lower()]

    if search:
        search_lower = search.lower()
        filtered = filtered[
            filtered["title"].str.lower().str.contains(search_lower)
            | filtered["abstract"].str.lower().str.contains(search_lower)
        ]

    total_count = len(filtered)
    page_items = filtered.iloc[offset : offset + limit].to_dict(orient="records")

    # Clean records
    clean_articles = []
    for item in page_items:
        clean_articles.append({
            "news_id": str(item.get("news_id", "")),
            "category": str(item.get("category", "General")),
            "subcategory": str(item.get("subcategory", "")),
            "title": str(item.get("title", "")),
            "abstract": str(item.get("abstract", "")),
            "url": str(item.get("url", "")),
        })

    return {
        "total": total_count,
        "offset": offset,
        "limit": limit,
        "articles": clean_articles,
    }


@router.get("/{news_id}", response_model=Dict[str, Any])
def get_news_article(news_id: str):
    """Retrieves details for a single news article."""
    df = get_cached_news_df()
    match = df[df["news_id"] == news_id]
    if match.empty:
        raise HTTPException(status_code=404, detail=f"News article {news_id} not found.")

    row = match.iloc[0].to_dict()
    return {
        "news_id": str(row.get("news_id", "")),
        "category": str(row.get("category", "General")),
        "subcategory": str(row.get("subcategory", "")),
        "title": str(row.get("title", "")),
        "abstract": str(row.get("abstract", "")),
        "url": str(row.get("url", "")),
    }
